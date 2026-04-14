# 🧩 Mental Health Platform – API Specification

---

## 📌 Overview

This platform provides a **comprehensive API layer** for three main applications:

1. **Admin Application**  
2. **Provider Application**  
3. **Client Application**

The backend is built using **FastAPI**, with modular architecture, PostgreSQL database, and external integrations like payment gateways and license verification APIs.


# Mental Health Platform - API Specification

**Version:** 1.0  
**Date:** April 09, 2026  
**Backend:** FastAPI + PostgreSQL  
**Authentication:** JWT Bearer Token

---

## 1. Authentication (`/auth`)

All registration and login endpoints.

| Method | Endpoint                        | Description                              | Access          | Response Model     |
|--------|---------------------------------|------------------------------------------|-----------------|--------------------|
| `POST` | `/auth/register/client`         | Register a new client                    | Public          | `Token`            |
| `POST` | `/auth/register/provider`       | Register a new provider                  | Public          | `Token`            |
| `POST` | `/auth/admin/register/admin`    | Create new admin (Super Admin only)      | Super Admin     | `MessageResponse`  |
| `POST` | `/auth/login`                   | Login with email + password              | Public          | `Token`            |
| `POST` | `/auth/logout`                  | Logout & blacklist token                 | Authenticated   | `MessageResponse`  |
| `GET`  | `/auth/me`                      | Get current user profile                 | Authenticated   | `UserMeResponse`   |
| `POST` | `/auth/verify-email`            | Verify email with code                   | Public          | `VerifyEmailResponse` |
| `POST` | `/auth/forgot-password`         | Send password reset link                 | Public          | `MessageResponse`  |
| `POST` | `/auth/reset-password`          | Reset password using token               | Public          | `MessageResponse`  |

---

## 2. Users (`/users`)

General user management (available to all roles with proper RBAC).

| Method | Endpoint                          | Description                                      | Access                  | Response Model          |
|--------|-----------------------------------|--------------------------------------------------|-------------------------|-------------------------|
| `GET`  | `/users/me`                       | Get own full profile                             | Any authenticated user  | `UserDetailResponse`    |
| `PUT`  | `/users/me`                       | Update basic user info                           | Any authenticated user  | `UserDetailResponse`    |
| `PUT`  | `/users/me/provider-profile`      | Update provider-specific profile                 | Provider                | `UserDetailResponse`    |
| `PUT`  | `/users/me/client-profile`        | Update client-specific profile                   | Client                  | `UserDetailResponse`    |
| `POST` | `/users/me/change-password`       | Change password (old password required)          | Any authenticated user  | `MessageResponse`       |
| `POST` | `/users/me/licenses`              | Add provider license                             | Provider                | `ProviderLicenseResponse` |
| `GET`  | `/users/`                         | List all users (paginated + filters)             | Admin / Super Admin     | `UserListResponse`      |
| `GET`  | `/users/{user_id}`                | Get any user by ID                               | Admin / Super Admin     | `UserDetailResponse`    |
| `PUT`  | `/users/{user_id}/status`         | Update user status (suspend/activate)            | Super Admin             | `UserDetailResponse`    |
| `PUT`  | `/users/{user_id}/publish`        | Toggle provider marketplace visibility           | Super Admin             | `UserDetailResponse`    |

---

## 3. Organizations (`/organizations`)

Multi-tenant clinic / group practice management.

| Method | Endpoint                              | Description                                      | Access                  | Response Model                     |
|--------|---------------------------------------|--------------------------------------------------|-------------------------|------------------------------------|
| `GET`  | `/organizations/me`                   | Get my organization                              | Any org member          | `OrganizationDetailResponse`       |
| `PUT`  | `/organizations/me`                   | Update organization (owner only)                 | Owner                   | `OrganizationDetailResponse`       |
| `PUT`  | `/organizations/me/settings`          | Update organization settings                     | Owner                   | `OrganizationSettingResponse`      |
| `PUT`  | `/organizations/me/branding`          | Update branding & colors                         | Owner                   | `OrganizationBrandingResponse`     |
| `PUT`  | `/organizations/me/billing`           | Update billing information                       | Owner                   | `OrganizationBillingInfoResponse`  |
| `GET`  | `/organizations/me/members`           | List organization members                        | Any org member          | `OrganizationMembersListResponse`  |
| `PATCH`| `/organizations/me/members/{member_id}` | Change member role                            | Owner                   | `OrganizationMemberResponse`       |
| `DELETE`| `/organizations/me/members/{member_id}`| Remove member                                 | Owner                   | `MessageResponse`                  |
| `POST` | `/organizations/me/invites`           | Send invite to new member                        | Owner                   | `OrganizationInviteResponse`       |
| `GET`  | `/organizations/me/invites`           | List pending invites                             | Owner                   | `OrganizationInvitesListResponse`  |
| `DELETE`| `/organizations/me/invites/{invite_id}`| Revoke invite                                 | Owner                   | `MessageResponse`                  |
| `POST` | `/organizations/invites/{token}/accept`| Accept invite                                  | Authenticated (email match) | `MessageResponse`              |
| `POST` | `/organizations/`                     | Create new organization (Super Admin)            | Super Admin             | `OrganizationDetailResponse`       |
| `GET`  | `/organizations/`                     | List all organizations (paginated)               | Super Admin             | `OrganizationListResponse`         |
| `GET`  | `/organizations/{org_id}`             | Get organization by ID                           | Org member / Super Admin| `OrganizationDetailResponse`       |
| `PUT`  | `/organizations/{org_id}`             | Update any organization                          | Super Admin             | `OrganizationDetailResponse`       |
| `PATCH`| `/organizations/{org_id}/status`      | Update organization status                       | Super Admin             | `OrganizationDetailResponse`       |
| `DELETE`| `/organizations/{org_id}`             | Soft delete organization                         | Super Admin             | `MessageResponse`                  |

---

## 4. Providers (`/providers`)

Provider-facing endpoints.

| Method | Endpoint                                   | Description                                      | Access   | Response Model                     |
|--------|--------------------------------------------|--------------------------------------------------|----------|------------------------------------|
| `GET`  | `/providers/me/dashboard`                  | Provider dashboard                               | Provider | `ProviderDashboardResponse`        |
| `GET`  | `/providers/me/availability`               | List availability slots                          | Provider | List[`ProviderAvailabilityResponse`] |
| `POST` | `/providers/me/availability`               | Add availability slot                            | Provider | `ProviderAvailabilityResponse`     |
| `PUT`  | `/providers/me/availability/{id}`          | Update availability                              | Provider | `ProviderAvailabilityResponse`     |
| `DELETE`| `/providers/me/availability/{id}`         | Delete availability                              | Provider | `MessageResponse`                  |
| `GET`  | `/providers/me/blocked-times`              | List blocked times / holidays                    | Provider | List[`ProviderBlockedTimeResponse`]|
| `POST` | `/providers/me/blocked-times`              | Block time range                                 | Provider | `ProviderBlockedTimeResponse`      |
| `DELETE`| `/providers/me/blocked-times/{id}`        | Delete blocked time                              | Provider | `MessageResponse`                  |
| `GET`  | `/providers/me/gallery`                    | List gallery items                               | Provider | List[`ProviderGalleryResponse`]    |
| `POST` | `/providers/me/gallery`                    | Add photo/video to gallery                       | Provider | `ProviderGalleryResponse`          |
| `DELETE`| `/providers/me/gallery/{id}`              | Delete gallery item                              | Provider | `MessageResponse`                  |
| `POST` | `/providers/me/publication-request`        | Request to be published in directory             | Provider | `ProviderPublicationRequestResponse` |
| `GET`  | `/providers/me/publication-status`         | Check publication status                         | Provider | `ProviderPublicationRequestResponse` |
| `GET`  | `/providers/me/waitlist`                   | View waitlist clients                            | Provider | List[`ProviderWaitlistResponse`]   |
| `GET`  | `/providers/me/reviews`                    | View received reviews                            | Provider | List[`ProviderReviewResponse`]     |
| `GET`  | `/providers/me/subscription`               | View current subscription                        | Provider | `ProviderSubscriptionResponse`     |

---

## 5. Executives (`/executives`)

Clinic owner / executive dashboard and clinic management.

| Method | Endpoint                              | Description                                      | Access   | Response Model                     |
|--------|---------------------------------------|--------------------------------------------------|----------|------------------------------------|
| `GET`  | `/executives/me/dashboard`            | Executive dashboard                              | Executive| `ExecutiveDashboardResponse`       |
| `GET`  | `/executives/me/staff`                | List clinic staff                                | Executive| List[`ClinicStaffResponse`]        |
| `POST` | `/executives/me/staff`                | Add new staff member                             | Executive| `ClinicStaffResponse`              |
| `PUT`  | `/executives/me/staff/{staff_id}`     | Update staff                                     | Executive| `ClinicStaffResponse`              |
| `DELETE`| `/executives/me/staff/{staff_id}`    | Deactivate staff                                 | Executive| `MessageResponse`                  |
| `GET`  | `/executives/me/announcements`        | List clinic announcements                        | Executive| List[`ClinicAnnouncementResponse`] |
| `POST` | `/executives/me/announcements`        | Create announcement                              | Executive| `ClinicAnnouncementResponse`       |
| `PUT`  | `/executives/me/announcements/{id}`   | Update announcement                              | Executive| `ClinicAnnouncementResponse`       |
| `DELETE`| `/executives/me/announcements/{id}`  | Delete announcement                              | Executive| `MessageResponse`                  |
| `GET`  | `/executives/me/permissions`          | View my permissions                              | Executive| List[`ExecutivePermissionResponse`]|
| `GET`  | `/executives/me/activity-logs`        | View activity logs                               | Executive| List[`ExecutiveActivityLogResponse`]|
| `POST` | `/executives/me/invite-staff`         | Invite new staff member                          | Executive| `MessageResponse`                  |

---

## 6. Clients (`/clients`)

Client-facing self-service endpoints.

| Method | Endpoint                                | Description                                      | Access   | Response Model                     |
|--------|-----------------------------------------|--------------------------------------------------|----------|------------------------------------|
| `GET`  | `/clients/me/dashboard`                 | Client dashboard                                 | Client   | `ClientDashboardResponse`          |
| `POST` | `/clients/me/assessments`               | Submit self-assessment                           | Client   | `ClientSelfAssessmentResponse`     |
| `GET`  | `/clients/me/assessments`               | List my assessments                              | Client   | List[`ClientSelfAssessmentResponse`]|
| `GET`  | `/clients/me/intake-forms`              | List completed intake forms                      | Client   | List[`ClientIntakeFormResponse`]   |
| `GET`  | `/clients/me/appointments`              | List my appointments                             | Client   | List[`ClientAppointmentResponse`]  |
| `POST` | `/clients/me/appointments`              | Request new appointment                          | Client   | `ClientAppointmentResponse`        |
| `DELETE`| `/clients/me/appointments/{id}`        | Cancel appointment                               | Client   | `MessageResponse`                  |
| `GET`  | `/clients/me/subscription`              | View my subscription                             | Client   | `ClientSubscriptionResponse`       |
| `GET`  | `/clients/me/goals`                     | List my therapy goals                            | Client   | List[`ClientGoalResponse`]         |
| `POST` | `/clients/me/goals`                     | Create new goal                                  | Client   | `ClientGoalResponse`               |
| `POST` | `/clients/me/goals/{goal_id}/progress`  | Record goal progress                             | Client   | `ClientProgressResponse`           |
| `GET`  | `/clients/me/journal`                   | List journal entries                             | Client   | List[`ClientJournalEntryResponse`] |
| `POST` | `/clients/me/journal`                   | Create journal entry                             | Client   | `ClientJournalEntryResponse`       |
| `GET`  | `/clients/me/medical-history`           | Get medical history                              | Client   | `ClientMedicalHistoryResponse`     |
| `PUT`  | `/clients/me/medical-history`           | Update medical history                           | Client   | `ClientMedicalHistoryResponse`     |
| `GET`  | `/clients/me/medications`               | List medications                                 | Client   | List[`ClientMedicationResponse`]   |
| `GET`  | `/clients/me/allergies`                 | List allergies                                   | Client   | List[`ClientAllergyResponse`]      |
| `GET`  | `/clients/me/preferences`               | Get preferences                                  | Client   | `ClientPreferenceResponse`         |
| `PUT`  | `/clients/me/preferences`               | Update preferences                               | Client   | `ClientPreferenceResponse`         |
| `GET`  | `/clients/me/consents`                  | List signed consents                             | Client   | List[`ClientConsentResponse`]      |
| `GET`  | `/clients/me/documents`                 | List uploaded documents                          | Client   | List[`ClientDocumentResponse`]     |
| `POST` | `/clients/me/documents`                 | Upload document                                  | Client   | `ClientDocumentResponse`           |
| `DELETE`| `/clients/me/documents/{id}`           | Delete document                                  | Client   | `MessageResponse`                  |

---

## Notes

- All protected routes require `Authorization: Bearer <token>` header.
- Pagination parameters (`skip`, `limit`) are supported where mentioned.
- Role-based access control is enforced in every endpoint.
- Background tasks are used for emails (verification, password reset, invites).
- Soft deletes are used throughout the system (`deleted_at`).

**Future Modules** (planned):
- `/sessions`
- `/payments`
- `/analytics`
- `/websites` (dynamic therapist websites)
- `/social` & `/referrals`

---

**End of Document**

