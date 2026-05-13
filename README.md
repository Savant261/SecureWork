# SecureWork - Enterprise B2B Freelance Marketplace & Escrow Engine 🚀

SecureWork is a production-ready freelance marketplace designed to solve the single biggest bottleneck in the gig economy: **Trust**.
SecureWork replaces insecure paper contracts with a cryptographic **Escrow Vault**. Clients deposit and lock funds safely before work begins, giving freelancers a 100% guarantee that the capital exists and is waiting for them upon approval.

By engineering a decoupled architecture with a focus on atomic transactions and Role-Based Access Control (RBAC), I built a platform that brings enterprise-level security and dynamic analytics to the freelancing workflow.

🔗 **Live Demo:** [https://secure-work.vercel.app/](https://secure-work.vercel.app/)

---

## 🔒 The Core Security Mechanism (How it Works)

1. **Contract Initialization**: A Client posts a job post. A Freelancer finds the job and submits an Application, proposing a specific list of milestones.
2. **Hiring**: When the Client clicks 'Accept Proposal', the backend generates a `Milestone` model in a `pending` state.
3. **Capital Injection**: Before the freelancer writes a single line of code, the client is required to click **'Fund Escrow'**. This is the key security event.
4. **Database Protection (`services.py`)**: To prevent race conditions or double-spending, the `fund_milestone` method in the Django backend actively locks the specific Wallet database row using **`select_for_update()`**. It then performs a transaction using Django's **`transaction.atomic()`** block:
    * It checks the client has sufficient liquid balance.
    * It debits the Client's liquid balance.
    * It credits the **Escrow Vault** for that specific contract.
    * It generates an immutable **'escrow_lock'** transaction record in the ledger.
    * It updates the Milestone status to `funded`.
    * *If any line of code fails during this entire sequence, the entire transaction is rolled back. Money can never be created or destroyed by a system error.*

5. **Payment Guarantee**: The freelancer can now safely begin work, knowing the funds are locked by the system and are waiting for them.
6. **Submission & Approval**: The freelancer submits their work (`Submission` model). The client reviews it.
7. **Auto-Resolution**: Once the Client clicks 'Release Funds', the system executes another atomic transaction, moving the capital from the Escrow Vault into the Freelancer's available balance and automatically updating the parent contract status to `completed` if all milestones are finalized.

This process eliminates the fear of non-payment for creators and ensures clients only pay for deliverables they actively approve.

---

## 🌟 Key Features

### ✨ System-Wide (Core Platform)

* 🛡️ **ACID Compliant Financial Logic**: All money handling logic is decoupled from views into `services.py`, leveraging `transaction.atomic()` and `select_for_update()` for 100% data integrity and zero race conditions.
* 🛡️ **Robust Authentication (SimpleJWT)**: Secured stateless API authentication using JSON Web Tokens with custom claims (role, identity).
* 🛡️ **Role-Based Access Control (RBAC)**: Strict separation of privileges between Clients and Freelancers via a custom database field; the API actively rejects unauthorized role actions.
* ⚡ **Zero-Latency Data Filtering**: Caches job board data and performs advanced search/budget filtering in the browser memory using Vanilla JS for instant visual feedback.
* 📊 **Dynamic Analytics (Chart.js)**: Line and breakdown doughnut charts render dynamic trajectory data directly from backend REST API stats. Upgraded glassmorphic tooltips for premium data visualization.

### 👩‍💻 For Freelancers

* 🌐 **Premium Portfolio Management**: A dedicated UI on the settings page to showcase GitHub links, portfolio URLs, professional titles, and tech stack skills.
* 📄 **Dynamic Bidding System**: Create proposals with a dynamically generated array of milestones, including custom titles, amounts, and due dates.
* 💸 **Dynamic Escrow Breakdown**: The Freelancer Wallet dynamically aggregates and displays the sum of all 'funded' and 'submitted' milestones from different clients, providing a clear picture of incoming revenue.
* 📦 **Deliverable Submissions**: Link proof-of-work (GitHub/Drive links, future: file attachments) to specific milestones for client review.

### 🏢 For Clients

* 🏗️ **Infrastructure Deployment**: Post detailed contracts with total budget allocations and project scopes.
* ✅ **Deliverable Review & Approval**: Review submitted proof-of-work and execute automated fund release with a single click.
* 🔔 **Action-Required Hub**: The main client dashboard actively lists contracts that require funding or approval, ensuring zero project bottlenecks.
* 💳 **Billing & Financial Management**: Link corporate payment methods and track all platform expenditures via the immutable ledger.

---

## 🗺️ System & User Journey Workflow

This flowchart illustrates the successful "Happy Path" lifecycle of a contract, highlighting how the platform acts as the secure bridge between both actors.

```mermaid
flowchart TD
    %% Define the main actors
    Client([Client User])
    Freelancer([Freelancer User])
    Platform[SecureWork API]

    %% The Journey
    Client -->|1. Posts Contract| Platform
    Platform -->|Published to| JobBoard[Marketplace Job Board]
    Freelancer -->|2. Finds Job & Bids| JobBoard
    Client -->|3. Hires Freelancer| Platform
    Platform -->|4. Generates Milestones| Milestones[Contract & Milestones Initialized]
    
    %% The Escrow Mechanism
    Milestones -->|5. Click 'Fund Escrow'| Funding{Payment Protocol}
    Funding -->|Capital Locked| Vault[(Secure Escrow Vault)]
    Vault -->|6. Status: Funded| Guarantee[Freelancer works with 100% Guarantee]
    
    %% The Work Phase
    Guarantee -->|7. Submits Deliverables| Platform
    Platform -->|Status: Submitted| Review{Client Reviews Work}
    
    %% Resolution
    Review -->|8. Click 'Release'| Platform
    Platform -->|Executes Release| Transfer[Automatic Transfer Protocol]
    Transfer -->|Credits| FreeWallet[Freelancer Wallet]
    Transfer -->|Records| Ledger[(Immutable Ledger)]
    Transfer -->|Updates Status| Complete([Contract Completed])
```

---

## 🏗️ Technical Architecture & Deployment

SecureWork is engineered as a strictly decoupled, three-tier architecture, isolating the Presentation layer from the Business Logic layer and the Data layer.

### Production Stack

| Layer | Technology | Host |
|---|---|---|
| **Frontend** | HTML, Vanilla JavaScript, Tailwind CSS | [Vercel](https://secure-work.vercel.app/) |
| **Backend API** | Python 3 / Django 6 / Django REST Framework | [Render](https://securework-api.onrender.com) |
| **Database** | PostgreSQL (managed) | [Supabase](https://supabase.com) (Asia-Pacific) |
| **Auth** | SimpleJWT (Access + Refresh tokens) | Render (via DRF) |

```mermaid
graph LR
    A["Vercel<br/>(Frontend)"] -->|REST API + JWT| B["Render<br/>(Django API)"]
    B -->|DATABASE_URL<br/>Transaction Pooler| C["Supabase<br/>(PostgreSQL)"]
```

**The Backend (REST API)**:
Powered by **Python/Django 6**, this is the central brain. It handles JWT authentication, performs complex financial accounting via atomic services, enforces Role-Based Access Control, and provides data statistics via REST endpoints. Deployed on Render with auto-deploy from the `main` branch. Database connection is managed via `dj-database-url` using Supabase's transaction pooler for reliable, persistent PostgreSQL hosting.

**The Frontend (JavaScript)**:
Built with **HTML, Vanilla JavaScript, and Tailwind CSS**. The entire UI communicates with the backend exclusively through asynchronous API calls via the central `app.js` controller. A custom DOM Notification Engine provides glassmorphic toast alerts for all system interactions, replacing standard browser alerts for a premium user experience. Deployed on Vercel with zero-config static hosting.

### Database Schema (ER Flowchart)

This is a connected, architectural flowchart showing how the backend data models interact. It focuses on relationships rather than field types.

```mermaid
flowchart TD
    %% Define the Database Tables (Nodes)
    Org([Organization])
    User([CustomUser])
    Wallet[(Wallet)]
    Tx[(Transaction)]
    Contract([Contract])
    App([Application])
    PMilestone([ProposedMilestone])
    Milestone([Milestone])
    Submission([Submission])

    %% Map the Relationships (Arrows)
    Org -->|Has Many Members| User
    User -->|1-to-1 Owns| Wallet
    Wallet -->|1-to-Many Records| Tx
    
    User -->|Client Posts 1-to-Many| Contract
    User -->|Freelancer Submits 1-to-Many| App
    
    Contract -->|Receives 1-to-Many| App
    App -->|Contains 1-to-Many| PMilestone
    
    Contract -->|Holds 1-to-Many| Milestone
    Milestone -->|1-to-1 Proof of Work| Submission
```

---

## 📂 File Structure

The project separates frontend assets from the Django application logic.

```text
/SecureWork
│
├── /backend                       # Django project root
│   ├── manage.py                  # Django administrative script
│   ├── requirements.txt           # Python dependencies
│   ├── build.sh                   # Render build script (migrate + superuser)
│   ├── db.sqlite3                 # Local SQLite fallback (dev only)
│   │
│   ├── /backend                   # Django project configuration
│   │   ├── settings.py            # Settings (JWT, CORS, dj-database-url, WhiteNoise)
│   │   ├── urls.py                # Root URL routing → /api/ and /admin/
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   └── /core                      # Core application (all business logic)
│       ├── models.py              # Organization, CustomUser, Wallet, Transaction,
│       │                          # Contract, Application, Milestone, Submission,
│       │                          # ProposedMilestone
│       ├── serializers.py         # DRF serializers (JWT, Register, Contract, etc.)
│       ├── views.py               # API views (Auth, Wallet, Contracts, Milestones)
│       ├── services.py            # Atomic FinanceService, RecruitmentService, WorkService
│       ├── permissions.py         # IsClient / IsFreelancer RBAC guards
│       ├── signals.py             # Auto Wallet creation on user registration
│       ├── tasks.py               # Scheduled auto-release for overdue milestones
│       ├── admin.py               # Django admin registrations
│       ├── apps.py                # AppConfig with signal import
│       └── urls.py                # API endpoint routing (Router + manual paths)
│
└── /frontend                      # Decoupled Presentation Layer
    ├── /js
    │   ├── app.js                 # Central controller: Dashboard, Wallet, Proposals,
    │   │                          # Toast Engine, UI Actions
    │   └── auth.js                # JWT token management & auth state
    │
    ├── /css
    │   └── styles.css             # Custom CSS rules
    │
    ├── /images                    # Static image assets
    ├── index.html                 # Premium fintech landing page
    ├── login.html                 # Authentication page
    ├── register.html              # Role-selection registration (Client/Freelancer)
    ├── dashboard.html             # User command center with Chart.js analytics
    ├── contracts.html             # Job board with live JS filtering
    ├── contract-detail.html       # Milestone timeline & proposal management
    ├── wallet.html                # Balance, escrow, deposit/withdraw & ledger
    └── settings.html              # Role-based tabbed user settings
```

---

## 🛠️ Installation & Setup

### Prerequisites

* Python 3.10+
* Git

### 1. Backend Setup (Django API)

**a. Clone the repository**:

```bash
git clone https://github.com/Savant261/SecureWork.git
cd SecureWork/backend
```

**b. Create a virtual environment & install dependencies**:

```bash
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

**c. Configure the database**:

For local development, the app defaults to SQLite — no setup needed. For PostgreSQL, set the `DATABASE_URL` environment variable:

```bash
# Windows (PowerShell)
$env:DATABASE_URL = "postgresql://user:password@host:port/dbname"

# macOS/Linux
export DATABASE_URL="postgresql://user:password@host:port/dbname"
```

**d. Run migrations & start the server**:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The Django REST API will be accessible at `http://127.0.0.1:8000/api/`.

### 2. Frontend Setup (Vanilla HTML/JS)

The frontend is a static site. Serve it with any static file server:

```bash
cd frontend
python -m http.server 3000
```

Open `http://127.0.0.1:3000` in your browser.

> **Note**: For local development, update `API_BASE` in `js/auth.js` and `js/app.js` from the production URL to `http://127.0.0.1:8000`.

### 3. Production Deployment

The production stack uses three separate services:

| Service | Platform | Config |
|---|---|---|
| **Frontend** | Vercel | Auto-deploys from `/frontend` directory |
| **Backend** | Render | Auto-deploys from `main` branch, runs `build.sh` |
| **Database** | Supabase | PostgreSQL via transaction pooler connection string |

**Render Environment Variables**:

| Key | Purpose |
|---|---|
| `DATABASE_URL` | Supabase PostgreSQL connection string (transaction pooler) |
| `DJANGO_SUPERUSER_USERNAME` | Auto-created admin username |
| `DJANGO_SUPERUSER_EMAIL` | Auto-created admin email |
| `DJANGO_SUPERUSER_PASSWORD` | Auto-created admin password |

---

## 🛠️ Future Roadmap

SecureWork is designed to scale. The next phases of development are focused on production hardening:

1. **Arbiter Role & Dispute Resolution**: Introduce a third 'Arbiter' (superuser) role. In the event of a dispute, this role can pause the contract, review submission records, and force-release funds based on arbitration.
2. **File Attachments for Submissions**: Upgrade the `Submission` model to handle actual `FileField` uploads for PDFs and source code zips.
3. **Real Profile Pictures**: Linking the `settings.html` dropzone to a backend `ImageField` on the `CustomUser` model.
4. **Contract-Specific Messaging Thread**: A real-time (WebSocket) or chronological comment thread on the contract detail page between client and freelancer.
5. **Automated Overdue Resolution**: Wire up `tasks.py` with Django-Celery-Beat for production-ready scheduled auto-release of milestone funds after 3 days of client inactivity.

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 👥 Authors

* **Savant Kumar Jena** - *Initial Work & Architectural Design* - 3rd Year CSE

### Acknowledgments

This project was built to explore advanced software architecture principles, the Django transactional model, and the decoupling of modern web applications. Thank you to the Django and Tailwind communities for the incredible tools and documentation!
