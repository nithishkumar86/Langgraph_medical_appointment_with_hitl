from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from src.Graphs.main_graph import get_main_graph
from langgraph.types import Command,Interrupt

app = FastAPI(title="MediBook API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
THREAD_ID = "1"  # Single session for entire app

class BookingRequest(BaseModel):
    question: str

class ConfirmBookingRequest(BaseModel):
    question: dict

class CancellationRequest(BaseModel):
    question: str

class ConfirmCancellationRequest(BaseModel):
    question: dict

# Initialize graph
graph = get_main_graph()

@app.get("/")
def root():
    return {"message": "MediBook API", "status": "active"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/start_booking")
def start_booking(request: BookingRequest):
    """Start booking workflow - calls LangGraph"""
    try:
        thread = {"configurable": {"thread_id": THREAD_ID}}
        
        # Invoke the graph
        response = graph.invoke(
            {"messages": [request.question]},
            config=thread
        )
        
        if "__interrupt__" in response and response["__interrupt__"]:
            hitl_data = response['__interrupt__'][0].value
            
            # Extract appointment details
            appointment = response.get('appointment')
            
            return {
                "hitl_data": {
                    "slots_available": appointment.slots_left if appointment else 0,
                    "next_slot_time": f"{appointment.start_time} - {appointment.end_time}" if appointment else "N/A",
                    "message": "Slots available. Please review and confirm.",
                    "hitl_response": hitl_data
                },
                "status": "user_confirmation"
            }
        
        return {"error": "Workflow completed without HITL"}
    
    except Exception as e:
        return {"error": str(e)}


@app.post("/confirm_booking")
def confirm_booking(request: ConfirmBookingRequest):
    """Confirm booking - resume graph with user decision"""
    try:
        thread = {"configurable": {"thread_id": THREAD_ID}}
        
        print(f"Received booking confirmation request: {request.question}")
        question = request.question

        action = question.get('action',None)
        detials = question.get('detials')

        
        final_response = graph.invoke(
        Command(resume={
            "action": action,
            "detials": detials
            }),
            config=thread
        )
    
        return {"status": "success", "result": final_response}
    except Exception as e:
        return {"error": str(e)}

@app.post("/start_cancellation")
def start_cancellation(request: CancellationRequest):
    """Start cancellation workflow"""
    try:
        thread = {"configurable": {"thread_id": THREAD_ID}}
        
        # question = f"cancel the booking for booking id {request.booking_id} for patient id {request.patient_id} and reason {request.reason}"
        question = request.question

        # Invoke the graph
        response = graph.invoke(
            {"messages": [question]},
            config=thread
        )
        
        # Check for HITL interruption
        if "__interrupt__" in response and response["__interrupt__"]:
            hitl_data = response['__interrupt__'][0].value
            
            return {
                "hitl_data": {
                    "type": hitl_data['type'],
                    "message": hitl_data['question'],
                    "detials": hitl_data['detials']
                },
                "status": "user_confirmation"
            }
        elif response.get('cancellation_router'):
            return {
                "message": "No HITL needed. Cancellation already performed.",
                "cancellation_result": response.get('cancellation_router'),
                "status": "success"
            }
        else:
            return {"error":"there is some error occured"}

    
    except Exception as e:
        return {"error": str(e)}

@app.post("/confirm_cancellation")
def confirm_cancellation(request: ConfirmCancellationRequest):
    """Confirm cancellation - resume graph with user decision"""
    try:
        thread = {"configurable": {"thread_id": THREAD_ID}}
        
        question = request.question
        # Resume graph with user input

        user_option = question.get('type')

        response = graph.invoke(
        Command(resume={
            "type": user_option
        }),config=thread
        )

        return {"response": response}
    
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 API running on http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)