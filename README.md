## 🏥 MediBook - Intelligent Medical Appointment System

A production-grade medical appointment booking platform built with LangGraph, FastAPI, and Streamlit. Features intelligent workflows, human-in-the-loop approvals, real-time email notifications, and complete observability.

Status: Production Ready ✅
Build Time: 2 weeks
Tech Stack: FastAPI • LangGraph • Streamlit • PostgreSQL • Docker • LangSmith

## 🎯 Overview
MediBook solves medical appointment complexity through:
Core Capabilities:

Intelligent routing between booking and cancellation requests
Human-in-the-Loop (HITL) approvals at critical decision points
Real-time insurance credential validation
Automated email confirmations via SMTP
Complete execution tracing with LangSmith
Handles 1000+ concurrent users with stateless design

Why This Project:
Production booking systems need more than CRUD. MediBook demonstrates building intelligent, observable systems that combine LLMs, business logic, human oversight, and enterprise reliability.

 ## Architecture
Workflow Subgraphs
Main Router → Intelligently routes requests

User Input → Router Decision → [Booking Path | Cancellation Path]



Booking Subgraph → Complete booking workflow

Start → booking_node → email_body_generator → send_email → End
  ├─ Question extraction & understanding
  ├─ Doctor availability checking
  ├─ Slot calculation
  ├─ HITL approval point
  └─ Confirmation email sent

Cancellation Subgraph → Complete cancellation workflow

Start → validate → cancellation_hitl → cancel_booking 
  → email_body → send_email → End
  ├─ Booking validation
  ├─ HITL cancellation approval
  ├─ Update booking status
  └─ Notification email sent

Email Body Generation → SMTP Delivery → Tracking

## ✨ Features
User Features:
✅ Appointment booking with real-time availability
✅ Insurance credential validation (database-backed)
✅ HITL approval before confirmation
✅ Automated confirmation emails
✅ Appointment cancellation with approval workflow
✅ Cancellation confirmation emails
✅ Clean, professional UI

## Technical Features:
✅ Multi-branch LangGraph routing
✅ Subgraph isolation (independent workflows)
✅ HITL interruption points
✅ Stateless API design (highly scalable)
✅ Type-safe code with Pydantic
✅ Complete LangSmith tracing
✅ Docker containerization
✅ Health checks & monitoring

## 🛠️ Tech Stack
Backend: FastAPI, LangGraph, SQLAlchemy, Pydantic
Frontend: Streamlit, Session State Management
Database: PostgreSQL, Psycopg2
Monitoring: LangSmith
Email: SMTP (Gmail, SendGrid compatible)

clone the Repository
```
git clone 
```
