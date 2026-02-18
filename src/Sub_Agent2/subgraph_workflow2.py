from langgraph.graph import StateGraph,START,END
from langchain_groq import ChatGroq
from typing_extensions import TypedDict,List,Literal,Annotated
from pydantic import BaseModel,Field
from datetime import date, time, datetime
from pydantic import BaseModel
from datetime import datetime, timedelta, time
import pandas as pd
from langchain_core.messages import SystemMessage
from datetime import datetime
import time
from langgraph.types import Command,interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import text
from sqlalchemy.engine import Engine
from src.Graph_States.graph_design import State,ConfirmCancellation,PatientCompleteBookingDetail
from src.Utils.model_loading import get_engine

engine = get_engine()


def validate_cancellation(state: State):
    booking_id = state["cancellation"].booking_id
    patient_id = state["cancellation"].patient_id

    query = """
        SELECT booking_id, patient_id, status, email_id
        FROM Patient_Bookings
        WHERE booking_id = %s
    """
    df = pd.read_sql(query, con=engine, params=(booking_id,))

    if df.empty:
        return {
            "cancellation_router": "Booking not found"
        }

    booking = df.iloc[0].to_dict()

    booking_email = booking.get("email_id")
    
    if booking["patient_id"] != patient_id:
        return {
            "cancellation_router": "Unauthorized cancellation attempt"
        }

    if booking["status"] == "cancelled":
        return {
            "cancellation_router": "Booking already cancelled"

        }

    if booking["status"] == "completed":
        return {
            "cancellation_router": "Completed booking cannot be cancelled"

        }

    return {
        "cancellation_router": "hitl","confirmcancellation": ConfirmCancellation(booking_id=booking_id, patient_id=patient_id, email_id =  booking_email,reason=state["cancellation"].reason)
    }


def router_for_hitl_path(state:State)->Literal["cancellation_hitl_node","__end__"]:
    if state['cancellation_router'] == "hitl":
        return "cancellation_hitl_node"
    else:
        return "__end__"


def cancellation_hitl(state: State):
    booking = state['cancellation'].booking_id
    question = state["messages"][-1]

    decision = interrupt(
        {
            "type": "approve or reject",
            "question": question,
            "detials": (
                f"Booking {booking} is active.\n"
                "Type `approve` to cancel the booking or `reject` to stop."
            )
        }
    )
    
    if decision['type'] == "approve":
        return {"cancellation_hitl_router": "approve"}
    else:
        return {"cancellation_hitl_router": "reject"}


def router_for_hitl_cancellation(state:State)->Literal["cancel_booking_node","__end__"]:
    if state['cancellation_hitl_router'] == "approve":
        return "cancel_booking_node"
    else:
        return "__end__"


def cancel_booking(state: State):
    final_result = None

    try:
        booking_id = state["confirmcancellation"].booking_id
        patient_id = state["confirmcancellation"].patient_id
        reason = state["confirmcancellation"].reason
        email_id = state["confirmcancellation"].email_id

        update_query = text("""
            UPDATE Patient_Bookings
            SET status = :status,
                cancelled_at = :cancelled_at,
                cancellation_reason = :reason
            WHERE booking_id = :booking_id
        """)

        with engine.begin() as conn:
            conn.execute(
                update_query,
                {
                    "status": "cancelled",
                    "cancelled_at": datetime.now(),
                    "reason": reason,
                    "booking_id": booking_id
                }
            )
        
        final_result = f"✅ Booking {booking_id} cancelled successfully\nPatient ID: {patient_id}\nEmail: {email_id}"

    except Exception as e:
        final_result = f"error cancelling booking: {str(e)}"

    return {
            "cancellation_result": final_result
        }


def router_for_booking_cancellation_email(state:State)->Literal['cancel_email_body_node','__end__']:
    if "error" in state['cancellation_result']:
        return '__end__'
    else:
        return 'cancel_email_body_node'


def cancel_email_body(state:State):
    booking_id = state["confirmcancellation"].booking_id
    patient_id = state["confirmcancellation"].patient_id
    reason = state["confirmcancellation"].reason
    email_id = state["confirmcancellation"].email_id

    email_body = f"""
    Dear Patient,

    Your cancellation request for booking ID {booking_id} has been approved.

    Details:
    - Patient ID: {patient_id}
    - Reason for Cancellation: {reason}
    
    If you'd like to reschedule, we're here to help."
    If you have any questions, please contact our support team.

    Best regards,
    Medical Appointment Team
    """

    return {"email_body": email_body.strip()}


def send_cancellation_email(state:State):
    # --- Email setup ---
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    if not SENDER_EMAIL:
        return "ERROR: SENDER_EMAIL not found in environment variables."
    
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
    if not SENDER_PASSWORD:
        return "ERROR: SENDER_PASSWORD not found in environment variables."

    # Create SMTP session
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)

    # --- Email content ---
    recipient_email = state["confirmcancellation"].email_id


    email_subject = "Your Appointment Cancellation Confirmation"
    email_body = state["email_body"] # Create email message

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = email_subject
    msg.attach(MIMEText(email_body, "plain")) # Send email
    try:
        server.send_message(msg)
        print(f"✅ Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"ERROR: Failed to send email - {e}")
    finally:
        server.quit()
