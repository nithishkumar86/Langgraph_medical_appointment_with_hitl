from pydantic import BaseModel,Field
from langchain_groq import ChatGroq
from config import Settings
from typing import List,Optional,Annotated,Literal,TypedDict
from pydantic import BaseModel, Field,model_validator
from datetime import date
from pydantic import BaseModel, field_validator
from datetime import time
from src.Utils.model_loading import get_model

llm = get_model()

class Router(BaseModel):
    route: Literal['booking','cancellation'] = Field(description="to classify either booking or cancellation")

with_structured_llm1 = llm.with_structured_output(Router)



class BookingUserInfo(BaseModel):
    consultation_type: Literal['initial', 'follow_up'] = Field(
        description="initial or follow_up"
    )

    insurance_status: Literal['active', 'expired', 'no'] = Field(description="insurance status whether active expired,no") 



    doctor_id: int = Field(
        description="Doctor ID to fetch doctor details"
    )

    check_date: date = Field(
        description="Date for checking slot availability"
    )

    @model_validator(mode="after")
    def validate_insurance_rules(self):
        if self.consultation_type == "initial" and self.insurance_status == "active":
            raise ValueError(
                "Insurance is not allowed for initial consultations"
            )
        return self
    

with_structured_llm2 = llm.with_structured_output(BookingUserInfo)

class DoctorDetail(BaseModel):
    doctor_id: int
    doctor_name: str
    specialization: str
    start_time: time
    end_time: time
    session: str


class AppointmentDetail(BaseModel):
    slots_left: int
    start_time: time
    end_time: time
    slot_minutes: int


class Cancellation(BaseModel):
    booking_id: int
    patient_id: int
    reason: str


with_structured_llm3 = llm.with_structured_output(Cancellation)


class Patient_Extraction(BaseModel):
    patient_name: str = Field(description="patient name")
    email_id:str = Field(description="email id from the user")

    
with_structured_llm4 = llm.with_structured_output(Patient_Extraction)



class PatientCompleteBookingDetail(BaseModel):
    patient_name: str
    doctor_id: int
    email_id: str
    appointmentdate: date
    start_time: time
    end_time: time
    consulation: Literal["initial", "follow_up"]
    insurance_status: Literal["active", "expired","no"]
    status: str


class ConfirmCancellation(BaseModel):
    booking_id: int = Field(description="booking id")
    patient_id : int = Field(description="patient id")
    email_id: str 
    reason: str = Field(description="reason for cancellation")


class State(TypedDict):
    messages: Annotated[List[str], "must contain at least 1 item"]
    router_to: str
    bookinguserinfo: BookingUserInfo
    doctordetail: DoctorDetail
    appointment: AppointmentDetail
    aggregator_result: str
    cancellation: Cancellation
    confirmcancellation: ConfirmCancellation
    cancellation_router:str
    cancellation_hitl_router: str
    cancellation_result: str
    patient_extraction: Patient_Extraction
    user_feedback: Literal["book",'recheck','end']
    patientcompletebookingdetail: PatientCompleteBookingDetail
    final_response: str
    email_body: str
