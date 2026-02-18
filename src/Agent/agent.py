import os
import sys
import time
from datetime import date,datetime, timedelta, time
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import text
from sqlalchemy.engine import Engine
from src.Graph_States.graph_design import State,ConfirmCancellation,PatientCompleteBookingDetail
from src.Utils.model_loading import get_engine,get_model
from src.Graph_States.graph_design import with_structured_llm1,with_structured_llm2,with_structured_llm3,with_structured_llm4
from src.Graph_States.graph_design import Router,DoctorDetail,AppointmentDetail,Cancellation
from langsmith import traceable

llm = get_model()

engine = get_engine()

@traceable(name="classifier",metadata={"classifier":"classify the user question"})
def classify_to_router(state:State):
    question = state["messages"][-1]
    response = with_structured_llm1.invoke(question)
    route = response.route
    return {"router_to": route}


@traceable(name="booking_question_extractor",metadata={"booking_question_extractor":"extract user details for booking"})
def question_extractor_for_booking(state: State):
    question = state["messages"][-1]

    response = with_structured_llm2.invoke(question)
    return {
        "bookinguserinfo": response
    }

@traceable(name="cancel_question_extractor",metadata={"cancel_question_extractor":"extract user details for cancel booking"})
def question_extractor_for_cancelling(state: State):
    question = state["messages"][-1]

    response = with_structured_llm3.invoke(question)
    return {
        "cancellation": response
    }
@traceable(name="doctor_availabilty",metadata={"doctor_availabilty": "fetch doctor availabilty fro the booking"})
def Fetch_doctor_availability(state: State):
    print("ENTER INTO DOCTOR AVAILABILTY")
    id = state['bookinguserinfo'].doctor_id

    def slots_availability(id):
        query = "SELECT * FROM doctor_availability WHERE doctor_id = %s"
        df = pd.read_sql(query, engine, params=(id,))  # Note: params should be a tuple
        
        if df.empty:
            return {"error": f"No availability found for doctor_id {id}"}
        
        record = df.to_dict(orient='records')[0]
        
        # Map database columns to DoctorDetail parameters
        mapped_data = {
            'doctor_id': record.get('doctor_id'),
            'doctor_name': record.get('doctor_name'),
            'specialization': record.get('specialization'),
            'start_time': record.get('start_time'),
            'end_time': record.get('end_time'),
            'session': record.get('session')
        }
        return mapped_data

    response = slots_availability(id)
    response = DoctorDetail(**response)

    return {"doctordetail": response}

@traceable(name="check_slots_remaining",metadata={"check_slots_remaining": "fetch slots availabilty fro the booking"})
def check_slots_remaining(state: State):

    print("ENTER INTO SLOT CHECKING")

    doctor_id = state["bookinguserinfo"].doctor_id
    appointment_date = state["bookinguserinfo"].check_date

    if state['bookinguserinfo'].consultation_type == "initial":
        slot_minutes = 60
    else:
        slot_minutes = 30

    doctor_start_time = state["doctordetail"].start_time
    doctor_end_time = state["doctordetail"].end_time

    if isinstance(appointment_date, str):
        appointment_date = datetime.strptime(
            appointment_date, "%Y-%m-%d"
        ).date()

    query = """
        SELECT start_time, end_time
        FROM Patient_Bookings
        WHERE doctor_id = %s
        AND appointment_date = %s
        ORDER BY end_time
    """
    df = pd.read_sql(query, engine, params=(doctor_id, appointment_date))

    cutoff_dt = datetime.combine(appointment_date, doctor_end_time)

    if df.empty:
        start_dt = datetime.combine(
            appointment_date, doctor_start_time
        )
    else:
        last_end_time = df["end_time"].max()
        start_dt = datetime.combine(
            appointment_date, last_end_time
        )

    end_dt = start_dt + timedelta(minutes=slot_minutes)

    if end_dt > cutoff_dt:
        return {
            "appointment":
                AppointmentDetail(
                    slots_left=0,
                    start_time=time(0,0),
                    end_time=time(0,0),
                    slot_minutes=slot_minutes
                )
        }

    remaining_slots = max(
        0,
        (cutoff_dt - start_dt) // timedelta(minutes=slot_minutes)
    )

    return {
        "appointment": 
            AppointmentDetail(
                slots_left = remaining_slots,
                start_time=start_dt.time(),
                end_time=end_dt.time(),
                slot_minutes=slot_minutes
            )
    }

@traceable(name="aggregator",metadata={"aggregator": "combine the user question"})
def aggragator_function(state:State):

    print("ENTER INTO AGGREGATOR")

    doctor_id = state["bookinguserinfo"].doctor_id
    appointment_date = state["bookinguserinfo"].check_date
    doctor_start_time = state["doctordetail"].start_time
    doctor_end_time = state["doctordetail"].end_time

    slots_left = state["appointment"].slots_left
    start_time = state["appointment"].start_time
    end_time = state["appointment"].end_time
    slot_minutes = state["appointment"].slot_minutes

    print(f'slots_left : {slots_left} slot_minutes: {slot_minutes}')
          
    if slots_left and start_time and end_time and slot_minutes:

        prompt = f"""You are a helpful medical appointment assistant.

            You will be given doctor availability and slot details.
            Your task is to generate a neat, clear, and user-friendly response
            that helps the patient decide whether to book or cancel an appointment.

            Use simple language.
            Do not expose raw data structures.
            Format the response clearly with headings and bullet points.
            If no slots are available, clearly mention that.

            Here is the information:

            Doctor ID: {doctor_id}
            Appointment Date: {appointment_date}

            Doctor Working Hours:
            - Start Time: {doctor_start_time}
            - End Time: {doctor_end_time}

            Slot Information:
            - Slots Left: {slots_left}
            - Next Available Slot Start Time: {start_time}
            - Next Available Slot End Time: {end_time}
            - Slot Duration (minutes): {slot_minutes}

            Instructions:
            1. Clearly show the doctor’s availability for the given date.
            2. If slots_left > 0, encourage the user to book and show the next available slot.
            3. If slots_left == 0, politely inform the user that no slots are available and suggest checking another date or doctor.
            4. End the response with a clear question asking whether the user wants to proceed with booking or cancel.
        """

        response = llm.invoke(prompt)
        return {"aggregator_result": response}
    else:
        return {"error occured"}

@traceable(name="booking_hitl",metadata={"booking_hitl": "human in the loop for booking"})
def Human_in_the_loop(state:State):
    result = state['aggregator_result']
    decision = interrupt({
        "action":"book or recheck or end",
        "detials":result
    })

    if decision.get('action') =='book':
        response = with_structured_llm4.invoke(decision['detials'])
        return {"patient_extraction": response, "user_feedback": "approve"}
    elif decision.get('action') =='recheck':
        return {"messages":[decision['detials']],"user_feedback": "recheck"}
    else:
        return {"user_feedback":"end"}

@traceable(name="booking_hitl_router",metadata={"booking_hitl_router": "router for hitl working"})
def hitl_router(state:State)->Literal['update_complete_booking_detail_node','question_extractor_for_booking_node','__end__']:
    if state['user_feedback'] == "approve":
        return "update_complete_booking_detail_node"
    elif state['user_feedback'] == "recheck":
        return "question_extractor_for_booking_node"
    else:
        return "__end__"
    
@traceable(name="updater",metadata={"updater": "update for the booking"})
def Update_Complete_Booking_Detail(state:State):
    patient_name = state['patient_extraction'].patient_name
    doctor_id = state['doctordetail'].doctor_id
    email_id = state['patient_extraction'].email_id
    appointmentdate = state['bookinguserinfo'].check_date
    start_time = state['appointment'].start_time
    end_time = state['appointment'].end_time
    consulation = state['bookinguserinfo'].consultation_type
    insurance_status = state['bookinguserinfo'].insurance_status
    status = "booked"

    return {"patientcompletebookingdetail":PatientCompleteBookingDetail(
            patient_name=patient_name,
            doctor_id=doctor_id,
            email_id=email_id,
            appointmentdate = appointmentdate,
            start_time=start_time,
            end_time=end_time,
            consulation=consulation,
            insurance_status = insurance_status,
            status=status
            
            )}

@traceable(name="condition_checker",metadata={"condition_checker": "router for question"})
def Condition_Check(state: State)->Literal['question_extractor_for_booking_node','question_extractor_for_cancelling_node']:

    if state['router_to'] == 'booking':
        return 'question_extractor_for_booking_node'
    else:
        return 'question_extractor_for_cancelling_node'
