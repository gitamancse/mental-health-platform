# Mental Health Platform – Frontend Architecture & Development Flow


---

## Recommended Approach (Senior Full Stack Recommendation)

**Single SPA (Single Page Application)** with **role-based routing and conditional dashboards**.

### Why Single SPA (not separate apps)?
- Maximum code reuse (shared UI components, auth logic, forms, etc.)
- Easier maintenance and deployment
- Fast switching between roles during development/testing
- One codebase for all user types (Admin, Executive, Provider, Client)
- Future micro-frontends possible if needed

**Alternative (only if required later):** Monorepo with Turborepo + separate apps (`admin-app`, `provider-app`, `client-app`).

---

## 🛠️ Tech Stack (Best Modern Choice 2026)

| Layer              | Technology                          | Reason |
|--------------------|-------------------------------------|--------|
| Framework          | React 18 + Vite + TypeScript        | Performance + Type safety |
| Routing            | React Router v6.26+                 | Nested layouts |
| State Management   | Redux Toolkit + RTK Query           | Best for API handling |
| UI Library         | shadcn/ui + Tailwind CSS            | Modern & accessible |
| Forms              | React Hook Form + Zod               | Fast validation |
| HTTP Client        | Axios (with interceptors)           | Token handling |
| Styling            | Tailwind + Radix UI                 | Clean UI |
| Authentication     | JWT + localStorage                  | Secure |
| Testing            | Vitest + RTL + MSW                  | Reliable |
| Code Quality       | ESLint + Prettier + Husky           | Clean code |

---

## 📁 Frontend Project Structure

```bash
frontend/
├── public/
├── src/
│   ├── app/
│   ├── assets/
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── common/
│   ├── features/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── organizations/
│   │   ├── executive/
│   │   ├── provider/
│   │   └── client/
│   ├── hooks/
│   ├── lib/
│   ├── pages/
│   ├── routes/
│   ├── store/
│   ├── types/
│   └── utils/
├── .env
├── vite.config.ts
└── package.json
```

---

## 🔐 Authentication Flow

- Login → `POST /auth/login`
- Store JWT in `localStorage` + Redux

### Axios Interceptor
- Attach `Authorization: Bearer <token>`
- Auto-refresh token on `401`
- Logout on token expiry

### Role-based Redirect
- `SUPER_ADMIN / ADMIN → /admin/dashboard`
- `EXECUTIVE → /executive/dashboard`
- `PROVIDER → /provider/dashboard`
- `CLIENT → /client/dashboard`

---

## 🛣️ Routing Strategy (React Router v6)

```tsx
const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { path: "login", element: <LoginPage /> },
      { path: "register/client", element: <ClientRegister /> },
      { path: "register/provider", element: <ProviderRegister /> },

      {
        path: "admin",
        element: <ProtectedRoute allowedRoles={["SUPER_ADMIN", "ADMIN"]} />,
        children: [{ path: "dashboard", element: <AdminDashboard /> }]
      },
      {
        path: "executive",
        element: <ProtectedRoute allowedRoles={["EXECUTIVE"]} />,
        children: [{ path: "dashboard", element: <ExecutiveDashboard /> }]
      },
      {
        path: "provider",
        element: <ProtectedRoute allowedRoles={["PROVIDER"]} />,
        children: [{ path: "dashboard", element: <ProviderDashboard /> }]
      },
      {
        path: "client",
        element: <ProtectedRoute allowedRoles={["CLIENT"]} />,
        children: [{ path: "dashboard", element: <ClientDashboard /> }]
      }
    ]
  }
]);
```

---

## 📊 Role-Based Dashboard Flow

| Role        | Path                  | Key Features |
|------------|----------------------|-------------|
| Client     | /client/dashboard    | Appointments, journal, goals |
| Provider   | /provider/dashboard  | Availability, reviews |
| Executive  | /executive/dashboard | Metrics, staff |
| Admin      | /admin/dashboard     | Users, analytics |

---

## 🔄 API Integration Strategy (RTK Query)

- Separate API slices:
  - `authApi`
  - `providerApi`
  - `clientApi`
  - `organizationApi`

- Benefits:
  - Auto hooks
  - Caching
  - Loading + error handling

### Example

```ts
export const providerApi = createApi({
  reducerPath: "providerApi",
  baseQuery: axiosBaseQuery(),
  endpoints: (builder) => ({
    getDashboard: builder.query({
      query: () => "/providers/me/dashboard",
    }),
  }),
});
```

---

## 🎯 Development Flow

### Phase 1 – Setup
- Setup Vite + React + TS
- Install Tailwind + Redux
- Setup Axios + Auth

### Phase 2 – Core UI
- Login / Register
- Layout (Sidebar/Navbar)

### Phase 3 – Dashboards
- Client, Provider, Admin dashboards

### Phase 4 – Features
- Appointments
- Journals
- Organizations

### Phase 5 – Polish
- Notifications
- Dark mode
- Responsive UI

---

## 📋 Best Practices

- Type safety from backend schemas
- Global error handling
- Skeleton loaders
- Accessibility (WCAG)
- Lazy loading
- Testing with MSW

---

## 🚀 Deployment

- Vercel (Recommended)
- Netlify (Alternative)

Environment:
```
VITE_API_URL=http://localhost:8000
```

---

## 🔄 Future-Proofing

- Micro-frontends ready
- Scalable architecture
- Easy separation later