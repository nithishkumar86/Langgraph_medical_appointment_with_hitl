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
from src.Graph_States.graph_design import State
from src.Utils.model_loading import get_engine

engine = get_engine()

def Booking_Node(state: State):
    final_result = None
    try:
        booking_details = state['patientcompletebookingdetail']

        insert_query = text("""
        INSERT INTO Patient_Bookings (
            patient_id,
            patient_name,
            doctor_id,
            email_id,
            appointment_date,
            start_time,
            end_time,
            appointment_type,
            insurance_status,
            status
        )
        VALUES (
            :patient_id,
            :patient_name,
            :doctor_id,
            :email_id,
            :appointment_date,
            :start_time,
            :end_time,
            :appointment_type,
            :insurance_status,
            :status
        );
    """)


        params = {
            "patient_id": 104,
            "patient_name": booking_details.patient_name,
            "doctor_id": booking_details.doctor_id,
            "email_id": booking_details.email_id,
            "appointment_date": booking_details.appointmentdate,
            "start_time": booking_details.start_time,
            "end_time": booking_details.end_time,
            "appointment_type": booking_details.consulation,
            "insurance_status": booking_details.insurance_status,
            "status": "BOOKED"
        }

        # Execute insert
        with engine.begin() as connection:
            connection.execute(insert_query, params)
            print("✅ Appointment Booked Successfully!")


        # Success message only
        final_result = f"""
        ✅ Appointment Booked Successfully!

        Patient Name      : {booking_details.patient_name}
        Doctor ID         : {booking_details.doctor_id}
        Appointment Date  : {booking_details.appointmentdate}
        Time Slot         : {booking_details.start_time} - {booking_details.end_time}
        Consultation Type : {booking_details.consulation}
        Status            : BOOKED
        """
    except Exception as e:
        final_result = f"error occured: {e}"

    return {
        "final_response": final_result.strip()
    }


def router_for_email_body_generator(state:State)->Literal['email_body_generator_node','__end__']:
    if "error" in state['final_response']:
        return '__end__'
    else:
        return 'email_body_generator_node'



def email_body_generator(state: State):
    booking_details = state["patientcompletebookingdetail"]

    email_body = f"""
    Dear {booking_details.patient_name},

    Your appointment has been successfully booked with the following details:

    Doctor ID         : {booking_details.doctor_id}
    Appointment Date  : {booking_details.appointmentdate}
    Time Slot         : {booking_details.start_time} - {booking_details.end_time}
    Consultation Type : {booking_details.consulation}

    Please arrive 10 minutes before your scheduled time.

    Thank you for choosing our service!

    Best regards,
    Medical Appointment Team
    """

    return {"email_body": email_body.strip()}

def send_email(state: State):

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
    recipient_email = state["patientcompletebookingdetail"].email_id 


    email_subject = "Your Appointment Booking Confirmation"
    email_body = state["email_body"] # Create email message

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = email_subject
    msg.attach(MIMEText(email_body, "plain")) # Send email
    try:
        server.send_message(msg)
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"ERROR: Failed to send email - {e}")
    finally:
        server.quit()
