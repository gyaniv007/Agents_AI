import os
from langgraph.graph import StateGraph, END
import uuid

# Import local modules based on our folder structure
from state import LoanState
import nodes
import edges

from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

def build_loan_graph():
    # 1. Initialize the Graph with our State schema
    workflow = StateGraph(LoanState)

    # 2. Add Nodes (The "Boxes" in your image)
    workflow.add_node("start_state_node", nodes.start_state_node)
    workflow.add_node("ingestion_agent", nodes.ingestion_agent)
    workflow.add_node("user_feedback", nodes.user_feedback_node)
    workflow.add_node("financial_analyst", nodes.financial_analyst_agent)
    workflow.add_node("risk_underwriter", nodes.risk_underwriter_agent)
    workflow.add_node("manual_review", nodes.manual_review_node)
    workflow.add_node("orchestrator", nodes.decision_orchestrator)
    workflow.add_node("sanctioned", nodes.sanctioned_node)
    workflow.add_node("not_sanctioned", nodes.not_sanctioned_node)
    workflow.add_node("conditional_approval", nodes.conditional_approval_node)

    # 3. Define the Flow (Edges)
    
    # Entry point
    workflow.set_entry_point("start_state_node")


    # Edge: Ingestion -> Feedback OR Analyst
    workflow.add_conditional_edges(
        "ingestion_agent",
        edges.route_after_ingestion,
        {
            "user_feedback": "user_feedback", 
            "financial_analyst": "financial_analyst"
        }
    )

    # Standard Edges
    workflow.add_edge("start_state_node", "ingestion_agent")
    workflow.add_edge("user_feedback", END)
    workflow.add_edge("financial_analyst", "risk_underwriter")

    # Edge: Risk -> Manual Review OR Orchestrator
    workflow.add_conditional_edges(
        "risk_underwriter",
        edges.route_after_risk_underwriter,
        {
            "manual_review": "manual_review", 
            "orchestrator": "orchestrator"
        }
    )

    # Final Decision Edge: Orchestrator -> Result Nodes
    workflow.add_conditional_edges(
        "orchestrator",
        edges.route_final_decision,
        {
            "sanctioned": "sanctioned",
            "not_sanctioned": "not_sanctioned",
            "conditional_approval": "conditional_approval"
        }
    )

    # All result nodes lead to END
    workflow.add_edge("sanctioned", END)
    workflow.add_edge("not_sanctioned", END)
    workflow.add_edge("conditional_approval", END)
    workflow.add_edge("manual_review", END)

    # 4. Compile the Graph
    return workflow.compile()


loan_app = build_loan_graph()

"""
if __name__ == "__main__":
    # Create the executable app
    app = build_loan_graph()

    #Create the LangGraph Flow Diagram
    png_bytes = app.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API,
    )
    with open("loan_workflow.png", "wb") as f:
        f.write(png_bytes)

    
    # Initial state to simulate a loan application
    initial_input = {
        "user_data": {"name": "Mr.Jack", "requested_amount": 50000},
        "status_message": "",
    }

    print("--- Starting Loan Sanction Process ---\n")
    
    #config = {"configurable": {"thread_id": str(uuid.uuid4()) } }
    #final_outcome = app.invoke(initial_input, config=config)


    # Run the graph and stream the steps

    for output in app.stream(initial_input):
        for key, value in output.items():
            print(f"Node '{key}' completed.")
            if "final_decision" in value:
                print(f"FINAL RESULT: {value['final_decision']}") 
"""
