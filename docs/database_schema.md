# Mental Health Platform – Database Schema

**Document Version:** 1.0  
**Last Updated:** April 2026  
**Database:** PostgreSQL + SQLAlchemy 2.0

---

## Overview

This document describes the complete database schema for the **Mental Health Platform** (Psychology Today-like system).

The schema is designed with the following principles:
- Single `users` table for all roles (Admin, Provider, Client)
- 1:1 profile tables for role-specific data
- Strong support for license verification across multiple states
- Compliance-ready audit logging
- Secure token management (JWT blacklisting)
- Flexible JSON fields for future extensibility

---

## 1. Table Summary

| Table Name                | Purpose |
|---------------------------|---------|
| `users`                   | Core user table – stores authentication and common user data for all roles |
| `admin_profiles`          | Admin-specific information (title, permissions, department) |
| `provider_profiles`       | Therapist / Provider detailed profile (bio, specialties, website, ratings, etc.) |
| `client_profiles`         | Client / Patient profile (preferences, self-assessment, membership) |
| `provider_licenses`       | Multi-state license records for providers |
| `provider_documents`      | Uploaded verification documents (licenses, degrees, certificates) |
| `blacklisted_tokens`      | JWT token revocation for secure logout |
| `audit_logs`              | Full audit trail for compliance and security |

---

## 2. Detailed Table Structures

### users (Core User Table)

| Column                     | Type              | Constraints          | Description |
|---------------------------|-------------------|----------------------|-----------|
| `id`                      | UUID              | PK                   | Unique user identifier |
| `email`                   | VARCHAR(255)      | Unique, Not Null     | Login email |
| `hashed_password`         | VARCHAR(255)      | Not Null             | Argon2id hashed password |
| `full_name`               | VARCHAR(255)      | Not Null             | Full legal name |
| `phone_number`            | VARCHAR(20)       | Nullable             | Contact number |
| `profile_picture_url`     | VARCHAR(500)      | Nullable             | Profile photo URL |
| `role`                    | ENUM              | Not Null             | `admin`, `provider`, `client` |
| `account_status`          | ENUM              | Not Null             | `pending`, `active`, `suspended`, `deleted` |
| `is_verified`             | BOOLEAN           | Default: false       | Admin verification status |
| `is_active`               | BOOLEAN           | Default: true        | Account active flag |
| `email_verified`          | BOOLEAN           | Default: false       | Email verification status |
| `mfa_enabled`             | BOOLEAN           | Default: false       | Multi-factor authentication |
| `verification_code`       | VARCHAR(20)       | Nullable             | Email verification code |
| `verification_code_expiry`| TIMESTAMP         | Nullable             | Code expiry time |
| `password_reset_token`    | VARCHAR(100)      | Nullable             | Password reset token |
| `password_reset_expiry`   | TIMESTAMP         | Nullable             | Reset token expiry |
| `last_login_at`           | TIMESTAMP         | Nullable             | Last successful login |
| `password_changed_at`     | TIMESTAMP         | Nullable             | Last password change |
| `created_at`              | TIMESTAMP         | Not Null             | Record creation time |
| `updated_at`              | TIMESTAMP         | Not Null             | Last update time |
| `deleted_at`              | TIMESTAMP         | Nullable             | Soft delete timestamp |

---

### admin_profiles

| Column              | Type       | Constraints     | Description |
|---------------------|------------|-----------------|-----------|
| `id`                | UUID       | PK              | Profile ID |
| `user_id`           | UUID       | FK → users      | Reference to user |
| `admin_title`       | VARCHAR    | Nullable        | Job title (e.g. "Platform Administrator") |
| `department`        | VARCHAR    | Nullable        | Department name |
| `is_super_admin`    | BOOLEAN    | Default: false  | Full system access |
| `permissions`       | JSONB      | Nullable        | Flexible permission settings |
| `created_at`        | TIMESTAMP  | Not Null        | Creation time |
| `updated_at`        | TIMESTAMP  | Not Null        | Last updated |

---

### provider_profiles

| Column                      | Type       | Constraints     | Description |
|-----------------------------|------------|-----------------|-----------|
| `id`                        | UUID       | PK              | Profile ID |
| `user_id`                   | UUID       | FK → users      | Reference to user |
| `professional_title`        | VARCHAR    | Not Null        | e.g. "Licensed Clinical Psychologist" |
| `years_of_experience`       | INTEGER    | Nullable        | Years of experience |
| `bio`                       | TEXT       | Nullable        | Professional biography |
| `specialties`               | JSONB      | Nullable        | Array of specialties |
| `modalities`                | JSONB      | Nullable        | Therapy approaches |
| `languages`                 | JSONB      | Nullable        | Spoken languages |
| `insurance_accepted`        | JSONB      | Nullable        | Accepted insurances |
| `office_address`            | TEXT       | Nullable        | Office location |
| `latitude`, `longitude`     | FLOAT      | Nullable        | Geolocation |
| `timezone`                  | VARCHAR    | Nullable        | Timezone |
| `subdomain_slug`            | VARCHAR    | Unique          | Personal website subdomain |
| `accepting_new_clients`     | BOOLEAN    | Default: true   | Currently accepting clients |
| `is_published`              | BOOLEAN    | Default: false  | Public visibility |
| `average_rating`            | FLOAT      | Default: 0.0    | Average client rating |
| `total_reviews`             | INTEGER    | Default: 0      | Total reviews received |
| `subscription_tier`         | VARCHAR    | Nullable        | `free`, `basic`, `premium` |
| `created_at`                | TIMESTAMP  | Not Null        | — |
| `updated_at`                | TIMESTAMP  | Not Null        | — |

---

### client_profiles

| Column                   | Type       | Constraints     | Description |
|--------------------------|------------|-----------------|-----------|
| `id`                     | UUID       | PK              | Profile ID |
| `user_id`                | UUID       | FK → users      | Reference to user |
| `date_of_birth`          | DATE       | Nullable        | Date of birth |
| `gender`                 | VARCHAR    | Nullable        | Gender |
| `preferred_language`     | VARCHAR    | Nullable        | Preferred language |
| `self_assessment_data`   | JSONB      | Nullable        | Self-assessment results |
| `preferences`            | JSONB      | Nullable        | Session & therapist preferences |
| `subscription_tier`      | VARCHAR    | Nullable        | Membership tier |
| `membership_expiry`      | TIMESTAMP  | Nullable        | Membership expiry date |
| `total_sessions`         | INTEGER    | Default: 0      | Total sessions attended |
| `created_at`             | TIMESTAMP  | Not Null        | — |
| `updated_at`             | TIMESTAMP  | Not Null        | — |

---

### provider_licenses

| Column            | Type       | Constraints     | Description |
|-------------------|------------|-----------------|-----------|
| `id`              | UUID       | PK              | License ID |
| `user_id`         | UUID       | FK → users      | Reference to provider |
| `license_number`  | VARCHAR    | Not Null        | License number |
| `state`           | VARCHAR(2) | Not Null        | State code (CA, NY, etc.) |
| `expiry_date`     | TIMESTAMP  | Nullable        | License expiry date |
| `is_verified`     | BOOLEAN    | Default: false  | Admin verification status |
| `verified_at`     | TIMESTAMP  | Nullable        | When verified |
| `verified_by`     | UUID       | Nullable        | Admin who verified |
| `created_at`      | TIMESTAMP  | Not Null        | — |

---

### provider_documents

| Column               | Type       | Constraints     | Description |
|----------------------|------------|-----------------|-----------|
| `id`                 | UUID       | PK              | Document ID |
| `user_id`            | UUID       | FK → users      | Reference to provider |
| `file_url`           | VARCHAR    | Not Null        | Azure Blob / storage URL |
| `file_type`          | VARCHAR    | Not Null        | `license`, `degree`, `photo`, etc. |
| `original_filename`  | VARCHAR    | Not Null        | Original file name |
| `uploaded_at`        | TIMESTAMP  | Not Null        | Upload timestamp |
| `verified`           | BOOLEAN    | Default: false  | Verification status |

---

### blacklisted_tokens

| Column        | Type       | Constraints     | Description |
|---------------|------------|-----------------|-----------|
| `id`          | UUID       | PK              | Record ID |
| `jti`         | VARCHAR    | Unique          | JWT Token ID |
| `user_id`     | UUID       | FK → users      | Owner of token |
| `expires_at`  | TIMESTAMP  | Not Null        | Expiry time |
| `created_at`  | TIMESTAMP  | Not Null        | — |

---

### audit_logs

| Column          | Type       | Constraints     | Description |
|-----------------|------------|-----------------|-----------|
| `id`            | UUID       | PK              | Log ID |
| `user_id`       | UUID       | FK → users      | Affected user |
| `action`        | VARCHAR    | Not Null        | Action name (e.g. `verify_therapist`) |
| `entity_type`   | VARCHAR    | Nullable        | Entity type |
| `entity_id`     | UUID       | Nullable        | Entity ID |
| `details`       | JSONB      | Nullable        | Additional context |
| `performed_by`  | UUID       | Not Null        | Admin who performed action |
| `ip_address`    | VARCHAR    | Nullable        | IP address |
| `created_at`    | TIMESTAMP  | Not Null        | Timestamp |

---

## Relationships Summary

- One `users` record can have **one** `admin_profiles`, `provider_profiles`, or `client_profiles` (1:1)
- One `users` record can have **many** `provider_licenses` and `provider_documents` (1:N)
- `users` has **many** `audit_logs` and `blacklisted_tokens` (1:N)

---

**Note:**  
All timestamp columns use `timezone=True`.  
JSONB fields are used for flexible, future-proof data storage.

You can copy this entire content and save it as **`docs/database_schema.md`** in your project.

Would you like me to also create:
- A **Mermaid ER Diagram** version for this schema?
- Or an updated `architecture.md` file?

Just let me know!