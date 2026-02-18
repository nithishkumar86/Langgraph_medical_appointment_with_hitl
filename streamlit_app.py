import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
import json

# Database connection
engine = create_engine("postgresql+psycopg2://postgres:nithish@localhost:5432/Crewai")

def credential_checking(insurance_provider: str, policy_number: str, policy_holder_name: str) -> str:
    """checking the credential value from the user"""
    if not all([insurance_provider, policy_number, policy_holder_name]):
        raise ValueError("One or more required details are missing")
    
    query = f"SELECT * FROM valid_insurance_policies WHERE policy_number = '{policy_number}'"
    
    df = pd.read_sql(query, con=engine)

    if df.empty:
        return "Error occurred there is no matching policy"
    else:
        result = df.to_dict(orient="records")
        if result[0]["insurance_provider"] == insurance_provider and result[0]["policy_number"] == policy_number and result[0]["policy_holder_name"] == policy_holder_name and result[0]["status"] == "active":
            return "active"
        else:
            return "expired"

st.set_page_config(
    page_title="MediBook - Appointment Using Langgraph",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    :root {
        --primary: #0066cc;
        --primary-light: #e6f0ff;
        --secondary: #00a86b;
        --text-dark: #1f2937;
        --text-light: #6b7280;
        --border: #e5e7eb;
        --success-light: #d1fae5;
    }
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .header-container {
        background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
        padding: 2.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
    }
    .header-container h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .info-item {
        background: #f9fafb;
        padding: 1rem;
        border-radius: 6px;
        border-left: 3px solid var(--primary);
    }
    .info-label {
        font-size: 0.85rem;
        color: var(--text-light);
        font-weight: 600;
        text-transform: uppercase;
    }
    .info-value {
        font-size: 1.1rem;
        color: var(--text-dark);
        margin-top: 0.4rem;
        font-weight: 500;
    }
    .divider {
        height: 1px;
        background: var(--border);
        margin: 2rem 0;
    }
    .hitl-section {
        background: #f0f9ff;
        border: 2px solid var(--primary);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 2rem 0;
    }
    .hitl-title {
        color: var(--primary);
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .confirmation-box {
        background: var(--success-light);
        border: 2px solid var(--secondary);
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    </style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://localhost:8000"

def init_session_state():
    defaults = {
        "consultation_type": None,
        "disease": None,
        "insurance_status": None,
        "selected_doctor_id": None,
        "appointment_date": None,
        "patient_name": None,
        "patient_email": None,
        "hitl_pending": False,
        "hitl_data": None,
        "booking_result": None,
        "show_patient_details": False,
        "cancellation_in_progress": False,
        "cancellation_booking_id": None,
        "cancellation_patient_id": None,
        "cancellation_reason": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

st.markdown("""
    <div class="header-container">
        <h1>⚕️ MediBook</h1>
        <p>Your intelligent medical appointment assistant</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📅 Book Appointment", "❌ Cancel Appointment"])

# ====================== BOOKING TAB ======================
with tab1:
    st.markdown("### Step 1: Tell us about your visit")
    
    st.session_state.consultation_type = st.selectbox(
            "Consultation Type",
            options=['initial', 'follow_up'],
            format_func=lambda x: "First Visit (Initial)" if x == 'initial' else "Follow-up Visit",
        )
    

    st.markdown("### Step 2: Insurance Information")
    
    if st.session_state.consultation_type == 'initial':
        st.warning("⚠️ Insurance cannot be used with initial consultations.")
        st.session_state.insurance_status = 'no'
    else:
        insurance_choice = st.radio(
            "Do you have health insurance?",
            options=['no', 'active', 'expired'],
            horizontal=True
        )
        
        if insurance_choice == 'active':
            st.markdown("#### Verify Your Insurance Details")
            
            col_ins1, col_ins2, col_ins3 = st.columns(3)
            
            with col_ins1:
                insurance_provider = st.text_input(
                    "Insurance Provider",
                    placeholder="e.g., Blue Cross, Aetna",
                    key="insurance_provider"
                )
            
            with col_ins2:
                policy_number = st.text_input(
                    "Policy Number",
                    placeholder="e.g., BC123456",
                    key="policy_number"
                )
            
            with col_ins3:
                policy_holder_name = st.text_input(
                    "Policy Holder Name",
                    placeholder="Full name as on policy",
                    key="policy_holder_name"
                )
            
            if st.button("🔍 Verify Insurance", type="primary", use_container_width=True, key="verify_insurance"):
                if insurance_provider and policy_number and policy_holder_name:
                    with st.spinner("Verifying insurance details..."):
                        try:
                            result = credential_checking(insurance_provider, policy_number, policy_holder_name)
                            st.session_state.insurance_status = result
                            
                            if result == "active":
                                st.success("✅ Insurance verified and active!")
                            else:
                                st.warning("⚠️ Insurance is expired")
                        except Exception as e:
                            st.error(f"Error verifying insurance: {str(e)}")
                else:
                    st.error("⚠️ Please fill all insurance details")
        else:
            st.session_state.insurance_status = insurance_choice
    
    st.markdown("### Step 3: Select Doctor & Date")
    
    doctor_data = {
        "Dr. Rajesh Kumar": {"id": 1, "spec": "Nephrologist (Kidney)", "hours": "9 AM - 1 PM"},
        "Dr. Priya Sharma": {"id": 2, "spec": "Cardiologist (Heart)", "hours": "1 PM - 5 PM"},
        "Dr. Arun Patel": {"id": 3, "spec": "General Physician", "hours": "5 AM - 9 PM"},
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_doctor_name = st.selectbox(
            "Select Doctor",
            options=list(doctor_data.keys())
        )
        selected_doctor = doctor_data[selected_doctor_name]
        st.session_state.selected_doctor_id = selected_doctor["id"]
        
        st.markdown(f"""
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Specialization</div>
                    <div class="info-value">{selected_doctor['spec']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Working Hours</div>
                    <div class="info-value">{selected_doctor['hours']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        min_date = datetime.now().date() + timedelta(days=1)
        max_date = min_date + timedelta(days=6)
        
        st.session_state.appointment_date = st.date_input(
            "Select Appointment Date",
            min_value=min_date,
            max_value=max_date,
        )
    
    if st.button("🔍 Check Availability", type="primary", use_container_width=True, key="check_avail"):
        if st.session_state.insurance_status:
            with st.spinner("Checking doctor availability..."):
                question = f"the user looking for booking and his consultation is {st.session_state.consultation_type} and patient have {st.session_state.insurance_status} insurance and user want to check Doctor ID {st.session_state.selected_doctor_id} available for appointments on {st.session_state.appointment_date}?"
                
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/start_booking",
                        json={"question": question},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if "error" not in data:
                            st.session_state.hitl_data = data.get("hitl_data")
                            st.session_state.hitl_pending = True
                            st.rerun()
                        else:
                            st.error(data.get("error", "Error checking availability"))
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
        else:
            st.warning("⚠️ Please verify insurance status before checking availability")
    
    if st.session_state.hitl_pending and st.session_state.hitl_data:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="hitl-section">
                <div class="hitl-title">✓ Review Your Appointment Availability</div>
        """, unsafe_allow_html=True)
        
        hitl_data = st.session_state.hitl_data
        st.markdown(f"""
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Doctor</div>
                    <div class="info-value">{selected_doctor_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Date</div>
                    <div class="info-value">{st.session_state.appointment_date}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Available Slots</div>
                    <div class="info-value">{hitl_data.get('slots_available', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Next Available Time</div>
                    <div class="info-value">{hitl_data.get('next_slot_time', 'N/A')}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.info(hitl_data.get('message', 'Review the availability above'))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Book", type="primary", use_container_width=True, key="confirm_book"):
                st.session_state.show_patient_details = True
                st.rerun()
        
        with col2:
            if st.button("🔄 Recheck", use_container_width=True, key="recheck_book"):
                st.session_state.hitl_pending = False
                st.session_state.hitl_data = None
                st.session_state.show_patient_details = False
                st.rerun()
        
        with col3:
            if st.button("❌ End", use_container_width=True, key="cancel_booking"):
                with st.spinner("Ending booking..."):
                    try:
                        confirm_data = {
                            "question": {
                                "type": "end",
                                "detials": "end booking"
                            }
                        }
                        
                        response = requests.post(
                            f"{API_BASE_URL}/confirm_booking",
                            json=confirm_data,
                            timeout=30
                        )
                        
                        st.session_state.hitl_pending = False
                        st.session_state.hitl_data = None
                        st.session_state.patient_name = None
                        st.session_state.patient_email = None
                        st.session_state.show_patient_details = False
                        st.info("Booking ended.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        if st.session_state.show_patient_details:
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown("#### Enter Your Details to Complete Booking")
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.patient_name = st.text_input(
                    "Full Name",
                    placeholder="John Doe",
                    key="hitl_name"
                )
            with col2:
                st.session_state.patient_email = st.text_input(
                    "Email Address",
                    placeholder="john@example.com",
                    key="hitl_email"
                )
            
            col_confirm1, col_confirm2 = st.columns(2)
            
            with col_confirm1:
                if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="confirm_booking_final"):
                    if st.session_state.patient_name and st.session_state.patient_email:
                        with st.spinner("Booking your appointment..."):
                            try:
                                question = f"for booking patient name is {st.session_state.patient_name} and email id is {st.session_state.patient_email}"
                                
                                confirm_data = {
                                    "question": {
                                        "action": "book",
                                        "detials": question
                                    }
                                }
                                
                                response = requests.post(
                                    f"{API_BASE_URL}/confirm_booking",
                                    json=confirm_data,
                                    timeout=30
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    booking_response = result.get("ressponse") or result.get("response")

                                    print("type",type(booking_response))
                                    
                                    # SAFE JSON PARSING - JUST DISPLAY WHATEVER WE GET
                                    if isinstance(booking_response, dict):
                                        st.session_state.booking_result = booking_response.get('final_response', 'Booking Successful')
                                    else:
                                        # If it's a string, don't try to parse it - just use it directly
                                        st.session_state.booking_result = 'Booking Successful'
                                    
                                        
                                    st.session_state.hitl_pending = False
                                    st.session_state.show_patient_details = False
                                    st.rerun()
                                else:
                                    st.error(f"Booking failed: {response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    else:
                        st.error("⚠️ Please enter your name and email")
            
            with col_confirm2:
                if st.button("❌ Cancel", use_container_width=True, key="cancel_patient_details"):
                    st.session_state.show_patient_details = False
                    st.session_state.patient_name = None
                    st.session_state.patient_email = None
                    st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.booking_result:
        st.markdown("""
            <div class="confirmation-box">
                <div class="confirmation-title">✅ Appointment Booked Successfully!</div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Patient</div>
                    <div class="info-value">{st.session_state.patient_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Doctor</div>
                    <div class="info-value">{selected_doctor_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Date</div>
                    <div class="info-value">{st.session_state.appointment_date}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(st.session_state.booking_result)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.booking_result = None
            st.session_state.patient_name = None
            st.session_state.patient_email = None
            st.session_state.show_patient_details = False
            st.rerun()

# ====================== CANCELLATION TAB ======================
with tab2:
    st.markdown("### Cancel Your Appointment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.cancellation_booking_id = st.text_input(
            "Booking ID",
            placeholder="Enter your booking ID",
        )
    
    with col2:
        st.session_state.cancellation_patient_id = st.text_input(
            "Patient ID",
            placeholder="Enter your patient ID",
        )
    
    st.session_state.cancellation_reason = st.text_area(
        "Reason for Cancellation",
        placeholder="Please tell us why you're cancelling...",
    )
    
    if st.button("🔍 Submit Cancellation Request", type="primary", use_container_width=True, key="submit_cancel"):
        if st.session_state.cancellation_booking_id and st.session_state.cancellation_patient_id:
            with st.spinner("Processing cancellation request..."):
                try:
                    question = f"cancel the booking for booking id {st.session_state.cancellation_booking_id} for patient id {st.session_state.cancellation_patient_id} and reason {st.session_state.cancellation_reason}"
                    
                    response = requests.post(
                        f"{API_BASE_URL}/start_cancellation",
                        json={"question": question},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if "error" not in data:
                            st.session_state.hitl_data = data.get("hitl_data")
                            st.session_state.cancellation_in_progress = True
                            st.rerun()
                        else:
                            st.error(data.get("error", "Error"))
                    else:
                        st.error(f"Error: {response.text}")
                except ValueError:
                    st.error("Please enter valid numeric IDs")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
        else:
            st.error("Please provide both IDs")
    
    if st.session_state.cancellation_in_progress and st.session_state.hitl_data:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="hitl-section">
                <div class="hitl-title">⚠️ Confirm Cancellation</div>
        """, unsafe_allow_html=True)
        
        hitl_data = st.session_state.hitl_data
        st.markdown(f"""
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Booking ID</div>
                    <div class="info-value">{st.session_state.cancellation_booking_id}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.warning(hitl_data.get('message', 'Confirm cancellation?'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Approve", type="primary", use_container_width=True, key="approve_cancel"):
                with st.spinner("Cancelling..."):
                    try:
                        confirm_data = {
                            "question": {
                                "type": "approve"
                            }
                        }
                        
                        response = requests.post(
                            f"{API_BASE_URL}/confirm_cancellation",
                            json=confirm_data,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.cancellation_in_progress = False
                            st.success("✅ Cancelled successfully!")
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("❌ Reject", use_container_width=True, key="reject_cancel"):
                with st.spinner("Processing..."):
                    try:
                        confirm_data = {
                            "question": {
                                "type": "reject"
                            }
                        }
                        
                        response = requests.post(
                            f"{API_BASE_URL}/confirm_cancellation",
                            json=confirm_data,
                            timeout=30
                        )
                        
                        st.session_state.cancellation_in_progress = False
                        st.info("Cancellation rejected. Appointment remains active.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
    <hr style="margin-top: 3rem;">
    <div style="text-align: center; padding: 2rem 0; color: #6b7280; font-size: 0.9rem;">
        MediBook © 2025
    </div>
""", unsafe_allow_html=True)