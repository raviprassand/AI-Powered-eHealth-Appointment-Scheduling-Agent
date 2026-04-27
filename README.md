# AI-Powered eHealth Appointment Scheduling Agent

An end-to-end eHealth platform that enables patients to interact using natural language to book appointments, retrieve medical records, and receive intelligent responses.

The system combines a modular **FastAPI backend** with a **React frontend**, enhanced with **LLM-based intent understanding** and **RAG-based patient context retrieval**.

---

## 🏗️ Architecture Overview

This repository is organized as a **monorepo** with two main branches:

- **`backend` branch** – FastAPI application responsible for:
  - Conversational appointment booking
  - LLM-based intent extraction
  - RAG-based patient data retrieval
  - Validation of patient, doctor, and schedule constraints
  - Writing notifications into `message_pat_to_doctor` table
  - Exposing REST APIs for the patient portal

- **`frontend` branch** – React-based patient and doctor portal:
  - Search & book appointments
  - View upcoming and past appointments
  - View notifications and error messages
  - View patient history and lab record history (enhanced UI)

> The `main` branch is used for documentation and integration notes.  
> Application source code is maintained in the **`backend`** and **`frontend`** branches.

---

## ✨ Key Features

- Conversational appointment booking using natural language
- LLM-based intent extraction for user requests
- RAG-based retrieval of patient-specific data (medical history, lab tests, prescriptions)
- Doctor selection based on `family_doctor_id`
- Appointment conflict detection and validation
- Storage of confirmed appointments in `appointment` table
- Notification creation in `message_pat_to_doctor` for portal display
- Enhanced UI for:
  - Patient history
  - Lab records
  - Booking failure handling
- Modular and scalable backend architecture

---

## 🤖 AI Components

The backend integrates AI in a controlled and safe manner:

- **LLM (Large Language Model)**  
  Used for understanding user intent and extracting structured information from natural language.

- **RAG (Retrieval-Augmented Generation)**  
  Retrieves patient-specific data before generating responses, ensuring accuracy and reducing hallucinations.

- **Deterministic Backend Logic**  
  Critical operations (e.g., appointment booking) are validated and executed by backend rules, not by the LLM.

---

## 🔀 Branch Structure

- `main` – Documentation and overview  
- `backend` – FastAPI backend service  
- `frontend` – React frontend application  

Switch branches using:

```bash
git checkout backend
git checkout frontend
