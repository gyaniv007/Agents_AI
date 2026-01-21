from state import LoanState


def route_after_ingestion(state: LoanState):
    """
    Corresponds to the 'Conditional Edge' after Ingestion Agent.
    Checks if format is valid or successful.
    """
    if state.get("status_message") == "Invalid Format":
        return "user_feedback"
    return "financial_analyst"

def route_after_risk_underwriter(state: LoanState):
    """
    Corresponds to 'Conditional Edge: Irregularities?'.
    Sends to Manual Review if True, otherwise to Decision Orchestrator.
    """
    if state.get("irregularities_found", False):
        return "manual_review"
    return "orchestrator"

def route_final_decision(state: LoanState):
    """
    Corresponds to 'Conditional Edge: DTI <= 40% & irregularity found?'.
    Logic:
    - Yes -> Sanctioned
    - No -> Not Sanctioned
    - Uncertain -> Conditional Approval
    """
    dti = state.get("dti_ratio", 1.0)

    if dti <= 0.40:
        return "sanctioned"
    elif dti > 0.60: # Example logic for 'No'
        return "not_sanctioned"
    else:
        return "conditional_approval"