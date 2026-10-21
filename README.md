# TakaTrack — Personal Expense & Budget Management Web Application (BDT / ৳)

TakaTrack is a full-stack personal finance manager tailored for people living in Bangladesh. It helps users manage their monthly budgets, daily expenses, loans, lending, fixed bills, and remaining money with precise decimal arithmetic.

---

## 🛠️ Technology Stack

### Frontend
* React
* TypeScript
* Vite
* Tailwind CSS[cite: 3]
* React Router[cite: 3]
* Axios[cite: 3]
* Lucide React[cite: 3]

### Backend
* Python 3[cite: 3]
* FastAPI[cite: 3]
* SQLAlchemy 2.0[cite: 3]
* Alembic (Database Migrations)[cite: 3]
* Pydantic v2[cite: 3]
* Argon2 (`pwdlib`) for secure password hashing[cite: 3]
* PyJWT (HTTP-Only Cookie Sessions)[cite: 3]

### Database
* PostgreSQL 16 (`Asia/Dhaka` timezone)[cite: 3]

---

## 📐 Financial Calculation Rules

1. **Total Ordinary Expenses** = `Daily Expenses + Paid Fixed Bills` (Unpaid bills, loans, and lending are never mixed into ordinary expenses, and paid bills are never double-counted)[cite: 3].
2. **Remaining Monthly Budget** = `Monthly Budget - Total Ordinary Expenses` (Can become negative when spending exceeds the budget)[cite: 3].
3. **Available Cash** = `Opening Cash + Inflows (Income + Loans Borrowed + Lending Repayments Received) - Outflows (Total Ordinary Expenses + Loan Repayments Made + Money Lent)`[cite: 3].

---

## 🚀 Running Locally on Apple Silicon (M-Series Mac)

### 1. Start PostgreSQL 16
```bash
brew services start postgresql@16
