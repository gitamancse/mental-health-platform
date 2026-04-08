# 🧠 Mental Health Platform

---

## 📌 Project Description

The **Mental Health Platform** is a **multi-tenant, scalable ecosystem** designed to support mental health services. It provides a complete suite of applications for **administrators, providers, and clients**, enabling:

- Provider registration, license verification, and subscription management  
- Client registration, session booking, and analytics dashboards  
- Continuous education content for providers and clients  
- Payments integration, referral network, and social features  

The platform is built with **modular architecture** to ensure scalability, maintainability, and enterprise-grade reliability.  

---

## ⚡ Key Features

### Admin Application
- User management (add/modify users and roles)  
- Provider management (approve registrations, publish/unpublish, configure features)  
- Subscription and discount management  
- System-wide analytics  

### Provider Application
- Multi-state license verification  
- Profile, website, and service configuration  
- Session management and appointments  
- Subscription plans (Free, Basic, Premium)  
- Education content management  

### Client Application
- Registration and login  
- Search providers and book sessions  
- Self-assessment toolkit  
- Subscription management and payments  
- Analytics dashboard  

### Shared Modules
- Payments (Stripe / Razorpay)  
- Sessions and appointments  
- Referrals and networking  
- Social engagement  
- Analytics and reporting  

---

## 🏗️ Tech Stack

| Layer          | Technology                         |
|----------------|-----------------------------------|
| Backend        | FastAPI, Python 3.11+             |
| Frontend       | React, Redux, TypeScript           |
| Database       | PostgreSQL                        |
| ORM            | SQLAlchemy, Alembic               |
| Authentication | JWT, Role-based Access (RBAC)     |
| Payments       | Stripe / Razorpay                  |
| Containerization | Docker, Docker Compose           |
| CI/CD          | GitHub Actions / GitLab CI        |

---

## 📂 Project Structure

```text
mental-health-platform/
├── app/               # Backend source code
├── frontend/          # React frontend
├── alembic/           # Database migrations
├── tests/             # Unit & integration tests
├── logs/              # Runtime logs
├── scripts/           # Helper scripts
├── docs/              # Documentation (architecture, API, DB schema, deployment)
├── .env               # Environment variables
├── docker-compose.yml # Docker orchestration
├── Dockerfile         # Backend container image
└── requirements.txt   # Python dependencies