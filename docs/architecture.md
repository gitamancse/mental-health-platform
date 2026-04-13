# 🧠 Mental Health Platform – System Architecture

## 📌 Overview

The **Mental Health Platform** is a **multi-tenant, role-based mental health ecosystem** that supports three primary user applications:

1. **Admin Application** (Super Admin)  
2. **Provider Application** (Therapists / Clinicians)  
3. **Client Application** (Patients / End Users)  

Additionally, it includes a **Clinic / Executive Application** for organization owners and staff.

The backend is built as a **modular monolith** using **FastAPI**, following **Domain-Driven Design (DDD)** principles and **Clean Architecture** patterns.

---

## 🏗️ High-Level Architecture

```
React + Redux (Frontend)
        ↓ (HTTPS + JWT)
FastAPI Backend (Modular Monolith)
        ↓
PostgreSQL (Single Source of Truth)
        ↓
External Services
├── Stripe / Razorpay (Payments)
├── License Verification APIs
└── Email Service
```

---

## 🧩 Core Principles

- Modular DDD
- Clean Architecture
- Multi-tenancy
- RBAC

---

## 📂 Project Structure

```bash
app/
├── core/
├── db/
├── modules/
├── utils/
└── middleware/
```

---

## 🗄️ Database

- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Soft deletes

---

## 🔐 Security

- JWT Auth
- RBAC
- Argon2 hashing

---

## 🚀 Roadmap

- Phase 1: Core modules
- Phase 2: Sessions, Payments
- Phase 3: Advanced features

---

## 🧠 Philosophy

> Strong domains, scalable system
