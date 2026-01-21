from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from main import loan_app

server = FastAPI()

class LoanRequest(BaseModel):
    name: str
    file_path: str
    amount: float

@server.post("/ai_loan")
async def process_loan(request: LoanRequest):
    # Prepare the initial state for LangGraph
    initial_state = {
        "user_data": {
            "name": request.name,
            "file_path": request.file_path,
            "requested_amount": request.amount
        }
    }
    
    try:
        # Run the graph (using ainvoke because FastAPI is async)
        final_state = await loan_app.ainvoke(initial_state)
        return final_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(server, host="127.0.0.1", port=8000)