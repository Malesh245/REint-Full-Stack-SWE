# WindSight ⚡ Technical Architecture & Code Review (Part 2)

> **Audience**: Internal Technical Lead / Engineering Peer Reviewer  
> **Speaker**: Lead Full-Stack Product Developer  
> **Duration**: ~4 to 5 minutes  
> **Goal**: Provide a clear, rigorous explanation of the software design, architecture, data engineering pipeline, statistical analytics, codebase organization, and key engineering practices.

---

## ⏱️ Video Script & Technical Walkthrough (0:00 – 4:45)

### Minute 0:00 – 0:50: Architectural Overview & Design Decisions
**[Visual: Architecture Diagram & Directory Structure]**

> *"Hi everyone. In this section, I’ll walk through the technical architecture, data pipelines, statistical algorithms, and codebase design for **WindSight**.*  
>
> *We chose a decoupled modern stack:*  
> - **Backend**: Python 3.12 with **FastAPI**. Python was chosen because energy time-series analytics require vectorized operations (Pandas, NumPy) and statistical distributions. FastAPI gives us high-throughput asynchronous I/O with automatic OpenAPI documentation.  
> - **Frontend**: **React** with **Vite** and **Recharts**. Recharts renders responsive SVG-based charts capable of rendering thousands of points smoothly without canvas overhead.  
> - **Reverse Proxy & Containers**: Multi-stage **Docker** containers orchestrated via **Docker Compose**, with Nginx handling SPA routing and API reverse-proxying."*

---

### Minute 0:50 – 1:50: Data Pipeline & Elexon BMRS Integration
**[Visual: Code walkthrough of `backend/app/services/elexon_client.py` and `analytics.py`]**

> *"Let’s look at the data ingestion and domain alignment challenges:*  
>
> **1. The Granularity Mismatch Challenge:**  
> - `FUELHH` (actual generation) is reported in **half-hour settlement periods** (48 per day).  
> - `WINDFOR` (forecasts) is reported on an **hourly cadence**.  
> - In `analytics.py::process_actuals()`, we floor the half-hourly timestamps to the hour and compute the arithmetic mean of the two half-hours ($\frac{HH_1 + HH_2}{2}$). This guarantees clean $1:1$ alignment without temporal leakage.  
>
> **2. High-Performance Concurrency & Two-Tier Caching:**  
> - Elexon BMRS stream endpoints can be slow for bulk range queries. If fetched sequentially, querying 31 days would take 30+ seconds.  
> - In `elexon_client.py`, we implemented asynchronous batching using `asyncio.gather` bounded by an `asyncio.Semaphore(10)`.  
> - We implemented a **two-tier cache**: an in-memory dictionary cache for hot endpoint calls, backed by a persistent disk cache (`data_cache/`) storing pre-validated JSON chunks. All 1,488 actual records and 19,272 forecast records for January 2026 are pre-warmed, delivering **sub-50 millisecond API latencies**."*

---

### Minute 1:50 – 2:50: Temporal Logic — Simulating True Day-Ahead Gate Closure
**[Visual: Code walkthrough of `backend/app/services/analytics.py::get_day_ahead_forecasts`]**

> *"A critical software requirement was: **How do we identify the true day-ahead forecast?**  
>
> In the UK wholesale market, traders participate in day-ahead auctions on day $D-1$ before gate closure (~09:00–11:00 UTC).  
> If you evaluate accuracy using a forecast published 2 hours before delivery, you are evaluating an *intraday* forecast, not a *day-ahead* decision.*  
>
> *In `get_day_ahead_forecasts()`:  
> ```python
> df['delivery_date'] = df['timestamp'].dt.date
> df['day_before_gate'] = df['timestamp'].dt.normalize() - pd.Timedelta(days=1) + pd.Timedelta(hours=9)
> day_ahead_mask = df['publish_time'] <= df['day_before_gate']
> ```  
> We compute the dynamic cutoff boundary at **09:00 UTC on day $D-1$** for each delivery hour. We then sort by `publish_time` descending and group by `timestamp`, taking `.first()`.  
> This guarantees that every single data point in our comparison and accuracy metrics reflects the **freshest available forecast at the exact moment of the auction commitment**."*

---

### Minute 2:50 – 3:45: Vectorized Statistical Analytics Engine
**[Visual: Walkthrough of `backend/app/services/analytics.py::compute_accuracy_metrics`]**

> *"Let’s examine how the metrics are calculated in `analytics.py`:  
>
> 1. **Vectorized Computations**:  
>    All calculations are vectorized across Pandas Series—no Python iteration loops:  
>    - $\text{MAE} = \text{mean}(|\text{Error}|)$  
>    - $\text{RMSE} = \sqrt{\text{mean}(\text{Error}^2)}$  
>    - $\text{MAPE} = \text{mean}(|\text{Error}| / \text{Actual}) \times 100\%$ with zero-division protection via `.replace(0, np.nan)`.  
>    - $\text{Bias} = \text{mean}(\text{Error})$  
>    - Pearson correlation coefficient between actuals and forecasts.  
>
> 2. **Flexible Grouping**:  
>    The `compute_accuracy_metrics()` function supports dynamic grouping: passing `group_by='hour_of_day'` groups by `timestamp.dt.hour`, while `group_by='day'` breaks down daily variations.  
>
> 3. **Statistical Distribution & Percentiles**:  
>    In `build_error_distribution()`, we calculate 30 histogram bins using `np.histogram` and compute non-parametric percentiles (5th, 10th, 25th, 50th, 75th, 90th, 95th) along with skewness and kurtosis. This provides traders with empirical value-at-risk (VaR) parameters."*

---

### Minute 3:45 – 4:45: Frontend Architecture, Dockerization & Code Quality
**[Visual: Walkthrough of `frontend/src/` and `docker-compose.yml`]**

> *"On the frontend:  
> - **Component Architecture**: Built around three distinct views: `DashboardView` (high-level KPIs & time-series), `AccuracyView` (statistical deep-dive & histograms), and `ForecastView` (forecast evolution over time).  
> - **State Management**: Clean unidirectional data flow. Date range state is lifted to `App.jsx` and synchronized across all views with debounced apply filters.  
> - **Production Readiness**:  
>   - Multi-stage Dockerfile: Node 20 alpine builds the static assets in under 5 seconds, copied into an ultra-lightweight Nginx alpine image.  
>   - Fully typed TypeScript/JavaScript configs with zero linter errors.  
>   - Docker Compose provisions both backend and frontend with built-in healthchecks.  
>
> To test the entire pipeline yourself, run `docker-compose up --build`, and the system is live on ports 3000 and 8000.  
>
> Thank you, and I’m ready for your questions."*

---

## 🛠️ Codebase Quick Reference for Reviewers

| Module | Key Functions / Components | Primary Responsibility |
|---|---|---|
| `backend/app/main.py` | FastAPI app, routes `/api/*`, lifespan | ASGI routing, response caching, parameter validation |
| `backend/app/services/elexon_client.py` | `fetch_wind_actuals`, `fetch_wind_forecasts` | HTTPX async client, connection pool, semaphore batching, disk cache |
| `backend/app/services/analytics.py` | `process_actuals`, `get_day_ahead_forecasts`, `compute_accuracy_metrics` | 30-to-60 min resampling, gate closure filter, MAE/RMSE/MAPE/Bias |
| `frontend/src/App.jsx` | Application container | View routing, global date-picker state |
| `frontend/src/views/DashboardView.jsx` | Line & composed charts, KPI metric cards | Actual vs Day-Ahead comparison & error timeseries |
| `frontend/src/views/AccuracyView.jsx` | Error histogram, percentiles, diurnal chart | Grouped statistical evaluation |
| `frontend/src/views/ForecastView.jsx` | Vintage progression charts | Multi-vintage forecast evolution |
| `docker-compose.yml` | `backend`, `frontend` services | Full-stack orchestration with healthchecks |
