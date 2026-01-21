from pydantic import BaseModel, Field
from typing import TypedDict, Optional, List


# Schema for the Underwriter's decision
class UnderwritingDecision(BaseModel):
    decision: str = Field(description="One of: 'Sanctioned', 'Not Sanctioned', 'Conditonal Approval', or 'Flag for Review'")
    irregularities_found: bool = Field(description="True if expenses are suspicious or DTI is critically high")
    summary: str = Field(description="Final summary of why this decision was made")

# Schema for the Analyst's output
class FinancialAnalysis(BaseModel):
    dti_ratio: float = Field(description="Debt-to-Income ratio calculated as total expenses / monthly income")
    financial_category: str = Field(description="Categorize as 'Stable', 'High Risk', or 'Moderate'")
    reasoning: str = Field(description="Brief explanation of the financial health assessment")

# Schema for the Ingestion Agents's Output
class ExtractedBankData(BaseModel):
    monthly_income: float = Field(description="Extract the transaction which mentions Monthly Salary")
    total_expenses: float = Field(description="Add all the expenses from the Bank Statement related to livelyhood and and office work")
    current_balance: float = Field(description="The ending balance on the statement")
    is_valid_statement: bool = Field(description="True if the Raw Content is a valid bank statement")

class UserData(TypedDict):
    name: Optional[str]
    email: Optional[str]
    mobile: Optional[str]
    requested_amount: float
    file_path: str
    monthly_income: float
    total_expenses: float
    current_balance: float

class LoanState(TypedDict):
    user_data: UserData
    raw_financial_text: str
    financial_metrics: Optional[dict]
    risk_assessment: Optional[dict]
    final_decision: Optional[str]
    irregularities_found: bool
    status_message: str
    is_stable: bool
    dti_ratio: float
    final_status: str
    financial_category: str
    reasoning: str