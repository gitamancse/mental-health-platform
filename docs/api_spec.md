# 🧩 Mental Health Platform – API Specification

---

## 📌 Overview

This platform provides a **comprehensive API layer** for three main applications:

1. **Admin Application**  
2. **Provider Application**  
3. **Client Application**

The backend is built using **FastAPI**, with modular architecture, PostgreSQL database, and external integrations like payment gateways and license verification APIs.

All endpoints follow a consistent structure:

```json
{
  "status": "success/error",
  "data": {},
  "message": ""
}