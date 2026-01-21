from nt import truncate
import random
import pandas as pd
from state import FinancialAnalysis, LoanState, ExtractedBankData, UnderwritingDecision, UserData
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from dotenv import load_dotenv
load_dotenv()

#ingestion_llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview")
struct_Ingestion_llm = ChatOpenAI(model="gpt-5-nano").with_structured_output(ExtractedBankData)
struct_fin_analysis_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(FinancialAnalysis)
struct_risk_assess_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_completion_tokens=500).with_structured_output(UnderwritingDecision)

#Start Node
def start_state_node(state: LoanState):
    print("--- 🧹 Clearing State for New Run ---")
    return state


#Extract Information from Bank Statement
def extract_text_from_file(file_path: str) -> str:
    """Helper to extract raw text based on file extension."""
    if file_path.endswith('.pdf'):
        reader = PdfReader(file_path)
        return " ".join([page.extract_text() for page in reader.pages])
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        return df.to_string()
    else:
        return ""

def ingestion_agent(state: LoanState):
    print("--- Ingesting Data ---")
    
    #Tie this to File to UI File Upload App
    file_path = state.get("user_data", {}).get("file_path")
    print("Bank Statement File Path : ", file_path)
    #file_path = "bank_statement.csv"

    if not file_path:
        return {"status_message": "Invalid Format", "user_data": state["user_data"]}

    # 1. Read & Parse Information
    raw_content = extract_text_from_file(file_path)
    print ("In INgestion: ", raw_content)
    # 2. Use LLM to extract/validate relevant info (Income, Balance, Transactions)
    system_message = f"""
    Act as an Financial Expert in reading Bank Statements efficiently. 
    Extract Monthly Income, Total Expense, and Current Balance from Raw Content {raw_content} only, 
    use the data from the raw content.
    For Total Expenses, add only the expenses related to livelyhood and office work related withdrawals.
    If the Raw Content is not a bank statement or is missing this info, reply with 'FAILURE'.
    Otherwise, reply with 'SUCCESS'. Along with the Extraction Information. 
    Response to be provided in the format specified.
    """
    
    try:
        # We use .invoke() here to trigger the LLM
        extraction = struct_Ingestion_llm.invoke(system_message) # Can use Truncate to save tokens
        print("Ingestion Agent : ", extraction)
        if extraction.is_valid_statement:
            # Update the existing user_data with the new extracted keys
            updated_user_data = {
                **state["user_data"],
                "monthly_income": extraction.monthly_income,
                "total_expenses": extraction.total_expenses,
                "current_balance": extraction.current_balance
            }

            return {
                "user_data": updated_user_data,
                "status_message": "SUCCESS",
                "raw_financial_text": raw_content
            }
        else:
            return {"status_message": "Invalid Format"}

    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"status_message": "Invalid Format"}

def user_feedback_node(state: LoanState):
    print("--- User Feedback: Error & Retry ---")
    return {"status_message": "Waiting for correct format"}

def financial_analyst_agent(state: LoanState):
    print("--- Financial Analysis ---")

    # 1. Get data from state
    income = state.get("user_data").get("monthly_income", 0)

    # 2. Safety check for Division by Zero
    if income <= 0:
        return {
            "status_message": "Invalid Financials",
            "dti_ratio": 1.0  # Default to max risk
        }

    # 3. Initialize llm for qualitative analysis
    
    system_promt = f"""
    You are a Senior Financial Analyst for loan approval. Analyze the user data {state['user_data']} &  
    {state['raw_financial_text']} for the following:
    - Monthly Salary
    - Total Expenses
    - Requested Loan

    Tasks:
    1. Calculate the DTI (Debt-to-Income) ratio strictly as (Expenses / Salary).
    2. Assess if the user's spending is sustainable.
    3. Categorize the user based on the DTI: 
       - DTI < 0.4: Stable
       - DTI 0.4 - 0.6: Moderate
       - DTI > 0.6: High Risk
    """

    # 4. Invoke LLM
    analysis = struct_fin_analysis_llm.invoke(system_promt)

    # 5. Update State
    print("Financial Analysis : ", analysis)
    return {
        "dti_ratio": analysis.dti_ratio,
        "financial_category": analysis.financial_category,
        "status_message": f"Analysis Complete: {analysis.reasoning}"
    }


def risk_underwriter_agent(state: LoanState):
    print("--- Risk Underwriting ---")
    # Simulate finding irregularities

    # 1. Gather data from previous nodes
    dti = state.get("dti_ratio", 0.0)
    category = state.get("financial_category", "Unknown")
    requested_amt = state.get("user_data", {}).get("requested_amount", 0)
    raw_statement = state.get("raw_financial_text", {})

    # 2. Initialize the Underwriter LLM
    system_prompt = f"""
    You are a Bank Risk Underwriter for Loan Sanction. Evaluate this loan application based on these internal policies:   
    POLICY:
    - If DTI > 0.6: Flag for Review or Reject.
    - If Financial Category is 'Stable' and DTI < 0.4: Proceed.
    - If the Loan Amount is > $50,000 and Category is 'Moderate', always 'Flag for Review'.
    - Go trough the Raw Statement and check for the irregularities in the transactions like anamoly in Withdrawals or Deposits

    APPLICATION DATA:
    - Debt-to-Income Ratio: {dti}
    - Financial Health: {category}
    - Requested Amount: {requested_amt}
    - Raw Statement: {raw_statement}

    Determine if we should Proceed, Reject, or if there are irregularities requiring 'Flag for Manual Review'.
    Give the underwriting reasoning summary in a crisp 4 line statement only.
    """

    # 4. Invoke LLM
    decision_data = struct_risk_assess_llm.invoke(system_prompt)
    print("Risk Underwright : ", decision_data)
    # 5. Update State
    # Note: 'irregularities_found' triggers the conditional edge to Manual Review
    return {
        "irregularities_found": decision_data.irregularities_found,
        "reasoning": f"Underwriting Complete: {decision_data.summary}",
        "status_message": decision_data.decision
    }

def manual_review_node(state: LoanState):
    print("--- Human-in-the-Loop: Manual Review ---")
    # Logic for officer to override
    return {"status_message": "Manual Review Completed", "final_decision": "Manual Review"}

def decision_orchestrator(state: LoanState):
    print("--- Decision Orchestration ---")
    return {"final_status": "Evaluating final criteria"}

def sanctioned_node(state: LoanState):
    print("--- Notify: Loan Sanctioned! ---")
    return {"final_decision": "Approved"}

def not_sanctioned_node(state: LoanState):
    print("--- Notify: Loan Rejected ---")
    return {"final_decision": "Rejected"}

def conditional_approval_node(state: LoanState):
    print("--- Requesting More Info ---")
    return {"final_decision": "Conditional"}

