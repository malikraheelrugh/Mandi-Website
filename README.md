# Mandi Broker Management System

Full-stack role-based stock and sales platform for a mandi broker workflow.

## Tech Stack

- Frontend: React + Bootstrap
- Backend: FastAPI (Python)
- Database: SQLite (development), PostgreSQL-ready via SQLAlchemy config
- Auth: JWT-based

## Features

### Roles

- **Admin**
  - Full access
  - Manage users (create/list/delete)
  - View stock, sales, reports, and dashboard metrics
- **Clerk**
  - Stock CRUD
  - Sell stock to buyers
  - Clerk actions are logged in audit logs
  - Sales visibility limited to own sales
- **Buyer**
  - Read-only view of own purchases
  - Cannot modify system data
  - JWT stored client-side in local storage

### Core Modules

- Stock management with negative stock prevention
- Sales with automatic stock deduction
- User management (admin-only)
- Admin reports (`daily`, `weekly`, `monthly`)

## Backend Setup (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Default seeded admin:

- Email: `admin@mandi.local`
- Password: `admin123`

## Frontend Setup (React)

```bash
npm install
npm run dev
```

Frontend expects backend at `http://localhost:8000`.

## API Endpoints

### Auth
- `POST /login`

### Users
- `GET /users`
- `POST /users`
- `DELETE /users/{id}`

### Stock
- `GET /stock`
- `POST /stock`
- `PUT /stock/{id}`
- `DELETE /stock/{id}`

### Sales
- `POST /sales`
- `GET /sales`
- `GET /sales/buyer/{id}`

### Extra
- `GET /dashboard/admin`
- `GET /reports/{period}` (`daily|weekly|monthly`)
- `GET /audit-logs`
