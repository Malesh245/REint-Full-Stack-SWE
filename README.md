# WindSight ⚡ UK Wind Power Forecast Analytics Platform

A production-grade full-stack web application designed for UK energy utility trading and procurement desks. WindSight enables day-ahead power traders to evaluate National Grid ESO / Elexon wind generation forecasts against outturn actuals, quantify forecast errors, and make data-driven wholesale power procurement decisions for January 2026.

---

## 🌟 Executive Summary & Problem Setting

In the UK electricity market, utility trading desks must procure sufficient electricity from the wholesale day-ahead market to serve consumer demand. Renewable sources like wind are inherently weather-dependent. Day-ahead purchase commitments are submitted prior to gate closure (~09:00–11:00 UTC on day $D-1$) for delivery across the 48 half-hour settlement periods of day $D$.

**WindSight** bridges the gap between raw forecasts and financial decisions:
1. **Decision Gate Alignment**: Isolates the exact forecast vintage available prior to day-ahead gate closure ($D-1$).
2. **Quantitative Error Evaluation**: Calculates standard industry metrics (MAE, RMSE, MAPE, Systematic Bias, Max Error, Correlation) to determine required thermal/peaker plant hedging margins.
3. **Forecast Evolution Analysis**: Visualizes how forecast accuracy evolves across multiple forecast publication runs (NGESO updates ~8 times daily) leading into the delivery hour.

---

## 🚀 Live Demo & Repository Links

- **Live Application**: [https://windsight-uk.vercel.app](https://windsight-uk.vercel.app) *(Deployment instructions below)*
- **Demo Video (Unlisted YouTube)**: [Watch the 10-Minute Pilot Pitch & Tech Review](#) *(Recorded per Section 3.1)*
- **Submission Repository**: [https://github.com/Malesh245/REint-Full-Stack-SWE](https://github.com/Malesh245/REint-Full-Stack-SWE)

---

## 🏗️ Architecture & Technology Stack

```
                     ┌───────────────────────────────────────────────┐
                     │           Client Browser (React SPA)          │
                     │  - Recharts Visualizations                    │
                     │  - Interactive Filtering (Jan 2026)          │
                     │  - KPI Cards & Error Distribution Histogram   │
                     └──────────────────────┬────────────────────────┘
                                            │ HTTP / JSON
                                            ▼
                     ┌───────────────────────────────────────────────┐
                     │          Reverse Proxy (Nginx) / CORS         │
                     │  - Port 80 / 3000                             │
                     └──────────────────────┬────────────────────────┘
                                            │
                                            ▼
                     ┌───────────────────────────────────────────────┐
                     │             FastAPI Backend (Python)          │
                     │  - Async / Concurrency (asyncio.gather)       │
                     │  - Pandas & NumPy Vectorized Analytics        │
                     │  - In-Memory & Persistent Disk Caching        │
                     └───────┬───────────────────────────────┬───────┘
                             │                               │
                             ▼                               ▼
       ┌───────────────────────────────┐   ┌───────────────────────────────┐
       │   Elexon BMRS FUELHH Stream   │   │   Elexon BMRS WINDFOR Stream  │
       │   Actuals (Half-Hourly WIND)  │   │   Forecasts (~8 Vintages/Day) │
       └───────────────────────────────┘   └───────────────────────────────┘
```

### Technology Breakdown
- **Frontend**:
  - React 18+ (SPA with Hooks and modular architecture)
  - Recharts for high-performance responsive SVG time-series, area charts, and bar histograms
  - Vanilla CSS tokens with modern glassmorphism, responsive grids, and dark theme
  - date-fns for ISO-8601 parsing and UTC date calculations
  - Axios for HTTP communication with client-side caching
- **Backend**:
  - FastAPI (Python 3.12+): Async ASGI framework
  - Pandas & NumPy: High-speed vectorized time-series resampling (30-min to 1-hour), alignment, and statistical error computation
  - HTTPX: Async connection pooling and HTTP client with retry logic
  - Pydantic v2 & Pydantic-Settings: Type-safe configuration management
- **Containerization & Deployment**:
  - Docker & Docker Compose: Multi-stage builds (Node alpine build -> Nginx alpine; Python 3.12-slim)
  - Vercel: Edge-optimized frontend static hosting
  - Local / Cloud Container Ready: Zero cloud-vendor lock-in

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py             # Settings, environment variables, CORS, date bounds
│   │   ├── main.py               # FastAPI application, route handlers, error handling
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── analytics.py      # Pandas analytics engine: MAE, RMSE, MAPE, bias, histograms
│   │       └── elexon_client.py  # Async Elexon BMRS client with concurrency & disk caching
│   ├── data_cache/               # Persistent pre-warmed January 2026 Elexon datasets
│   │   ├── fuelhh_*.json         # 31 days of outturn wind generation actuals
│   │   └── windfor_*.json        # 33 chunks of wind forecast publication vintages
│   ├── Dockerfile                # Production Python 3.12 container
│   └── requirements.txt          # Pinned backend dependencies
├── frontend/
│   ├── public/                   # Static assets & icons
│   ├── src/
│   │   ├── api.js                # Axios API client layer with environment resolution
│   │   ├── App.jsx               # Application shell, navigation, global date picker
│   │   ├── index.css             # Design system, CSS variables, glassmorphism UI
│   │   ├── main.jsx              # React DOM root entry
│   │   └── views/
│   │       ├── DashboardView.jsx # Actual vs Forecast comparison, KPIs, error stream
│   │       ├── AccuracyView.jsx  # Metric breakdown by hour/day, error histogram, percentiles
│   │       └── ForecastView.jsx  # Multi-vintage forecast evolution per delivery date
│   ├── Dockerfile                # Multi-stage build (Node build -> Nginx server)
│   ├── nginx.conf                # Nginx reverse proxy configuration
│   ├── package.json              # Frontend scripts and dependencies
│   ├── vercel.json               # Vercel SPA routing configuration
│   └── vite.config.js            # Vite build and dev proxy configuration
├── docker-compose.yml            # Multi-container orchestration (Frontend + Backend)
├── PRESENTATION_PITCH.md         # Deliverable 3.1 Part 1: Client pilot presentation script
├── TECH_LEAD_REVIEW.md           # Deliverable 3.1 Part 2: Tech lead architecture & code review
└── README.md                     # Comprehensive project documentation
```

---

## ⚡ Quick Start: Running the Application

### Option 1: Docker Compose (Recommended - Single Command)

The easiest way to run the full application with all services:

```bash
# Clone the repository
git clone <repo-url>
cd <repo-folder>

# Start both backend (FastAPI) and frontend (Nginx)
docker-compose up --build
```

- **Frontend Application**: Open [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger)**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check**: Open [http://localhost:8000/](http://localhost:8000/)

To stop the services:
```bash
docker-compose down
```

---

### Option 2: Running Locally (Development Mode)

#### 1. Backend Setup (Python)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI with live reload
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

#### 2. Frontend Setup (React / Vite)

In a new terminal window:
```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
The frontend will open at [http://localhost:3000](http://localhost:3000) (or `http://localhost:5173`) with live hot-module replacement and API proxying configured.

---

## 📊 Analytics & Domain Methodology

### 1. Market Mechanism & Day-Ahead Forecast Extraction
In Great Britain, the electricity day is divided into 48 settlement periods of 30 minutes each (Half-Hour / HH). Day-ahead power exchange auctions (such as EPEX SPOT and Nord Pool) close between 09:20 and 11:00 UTC on day $D-1$.
- **FUELHH (Actuals)**: Published at 30-minute intervals. Aggregated to hourly average MW ($\frac{\text{HH}_1 + \text{HH}_2}{2}$) to match the WINDFOR forecast resolution.
- **WINDFOR (Forecasts)**: Published ~8 times per day (03:30, 05:30, 08:30, 10:30, 12:30, 16:30, 19:30, 23:30 UTC) for delivery horizons spanning up to 72+ hours.
- **Day-Ahead Vintage Filter**: To replicate real procurement conditions, WindSight filters for the latest forecast published **before 09:00 UTC on day $D-1$** for each delivery hour on day $D$.

### 2. Quantitative Accuracy Metrics
For actual outturn $A_t$ and day-ahead forecast $F_t$ across $N$ hourly settlement points:

$$\text{Error}_t = F_t - A_t$$

- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{t=1}^N |F_t - A_t|$$
  Measures overall magnitude of procurement discrepancy in MW.

- **Root Mean Square Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{t=1}^N (F_t - A_t)^2}$$
  Penalizes large errors heavily, critical for balancing grid stress.

- **Mean Absolute Percentage Error (MAPE)**:
  $$\text{MAPE} = \frac{1}{N} \sum_{t=1}^N \left| \frac{F_t - A_t}{A_t} \right| \times 100\%$$
  Relative error scale across varying wind regimes.

- **Systematic Bias**:
  $$\text{Bias} = \frac{1}{N} \sum_{t=1}^N (F_t - A_t)$$
  Positive bias indicates systematic over-forecasting (requiring costly cash-out imbalance purchases); negative bias indicates systematic under-forecasting.

- **Error Distribution & Percentiles**:
  Evaluates 5th, 10th, 25th, 50th (median), 75th, 90th, and 95th percentiles to determine the reserve thermal capacity buffer required for 95% confidence intervals.

---

## 🌐 REST API Specification

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/` | `GET` | None | Service health status and metadata |
| `/api/actuals` | `GET` | `date_from`, `date_to` | Hourly wind actual generation (FUELHH) |
| `/api/forecasts` | `GET` | `date_from`, `date_to` | All forecast vintages + selected day-ahead forecast |
| `/api/comparison` | `GET` | `date_from`, `date_to` | Merged time-series of actuals vs day-ahead forecast with error |
| `/api/accuracy` | `GET` | `date_from`, `date_to`, `group_by` | MAE, RMSE, MAPE, Bias, percentiles, and error histogram |
| `/api/forecast-evolution` | `GET` | `target_date` | Multi-vintage forecast progression across publish times |
| `/api/cache` | `DELETE` | None | Flushes in-memory cache |

---

## 🚢 Deployment Guide

### Deploying Full-Stack (Frontend + Backend) to Vercel (1-Click)

The repository is pre-configured with root [`vercel.json`](./vercel.json) and serverless function [`api/index.py`](./api/index.py) to deploy **both the React frontend and FastAPI backend together on Vercel** under a single domain:

1. Go to **[vercel.com](https://vercel.com)** and sign in with your GitHub account.
2. Click **"Add New Project"** and select **`REint-Full-Stack-SWE`**.
3. Leave all settings as default (root directory `.`, framework auto-detected).
4. Click **"Deploy"**.
5. In ~45 seconds, Vercel will build the React frontend and configure the Python serverless API under a single live URL (e.g., `https://reint-full-stack-swe.vercel.app`).
   - Frontend: `https://<your-project>.vercel.app/`
   - API Endpoints: `https://<your-project>.vercel.app/api/*`

### Alternative: Docker & Container Hosting (Koyeb / Railway / Heroku)

If container-based hosting is desired:
- **Koyeb**: Connect repository, set root directory to `backend`, builder to `Docker`, port `8000` (Free 24/7 without sleeping).
- **Heroku**: Uses [`backend/Procfile`](./backend/Procfile) and [`backend/runtime.txt`](./backend/runtime.txt).
- **Docker Compose**: Run `docker-compose up --build` on any Linux/Cloud VPS.

---

## 🤖 Disclosure of AI Tools Used

In accordance with Section 2 of the challenge instructions, the following AI tools and pair-programming assistants were utilized during the development of this application:
- **Google Antigravity IDE / Gemini 3.8 Flash (High) / Claude Opus**: Used for code scaffolding, accelerated exploratory API analysis of Elexon BMRS documentation, statistical aggregation formulas, and writing documentation artifacts.
- All domain logic (UK day-ahead market timing, gate closure rules, Elexon BMRS schema mapping, and error quantification) was architected and verified against official Elexon specifications and industry balancing guidelines.

---

## 📄 Challenge Deliverables Checklist

- [x] **Working Full-Stack Application**: React frontend + Python FastAPI backend
- [x] **January 2026 Scope**: National-level Elexon BMRS data (`FUELHH` actuals & `WINDFOR` forecasts)
- [x] **Quantified Forecast Accuracy**: MAE, RMSE, MAPE, Bias, Max Error, Correlation, Error Distribution
- [x] **Dockerized**: Multi-stage `Dockerfile`s and `docker-compose.yml`
- [x] **Section 3.1 Part 1 Presentation**: Client pilot presentation script in [`PRESENTATION_PITCH.md`](./PRESENTATION_PITCH.md)
- [x] **Section 3.1 Part 2 Tech Lead Review**: Architecture and implementation review in [`TECH_LEAD_REVIEW.md`](./TECH_LEAD_REVIEW.md)
- [x] **Section 3.2 Public Repo README**: Comprehensive file index, setup instructions, and deployment details
