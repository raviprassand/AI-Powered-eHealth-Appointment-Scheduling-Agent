# AI-Powered eHealth Appointment Scheduling Agent

An end-to-end eHealth platform that helps patients book and manage appointments with family doctors and specialists.  
The system uses a modular **FastAPI backend** and a **React frontend**, with integrations to a relational database and notification tables for portal alerts.

---

## 🏗️ Architecture Overview

This repository is organized as a **monorepo** with two main branches:

- **`backend` branch** – FastAPI application for:
  - Booking appointments
  - Validating patient, doctor, and schedule information
  - Writing notifications into `message_pat_to_doctor` table
  - Exposing REST APIs for the patient portal

- **`frontend` branch** – React-based patient and doctor portal:
  - Search & book appointments
  - View upcoming and past appointments
  - View notifications and error messages when booking fails
  - View patient history and lab record history (improved UI)

> The `main` branch is used as the documentation and integration branch.  
> Application source code lives in the **`backend`** and **`frontend`** branches.

---

## ✨ Key Features

- Patient login and appointment scheduling
- Doctor selection based on `family_doctor_id` and availability
- Storage of confirmed appointments in `dev1.appointment`
- Creation of notification messages in `message_pat_to_doctor` for portal display
- Improved UI for:
  - Patient history
  - Lab record history
  - Error messages when appointment booking fails
- Separate, clean codebases for backend and frontend

---

## 🔀 Branch Structure

- `main` – Documentation, high-level overview, and integration notes
- `backend` – FastAPI backend service  
- `frontend` – React frontend application

You can switch branches using:

```bash
git checkout backend     # for backend code
git checkout frontend    # for frontend code
