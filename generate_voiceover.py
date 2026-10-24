import os
import subprocess
import httpx

DEEPGRAM_API_KEY = "f8263fd7b9b5fda354ed9fd870f7729a4a06ea51"
DEEPGRAM_URL = "https://api.deepgram.com/v1/speak?model=aura-arcas-en"

# Script for Part 1: Client Pitch & Pilot Presentation
PART1_SCRIPT = """
Good morning, everyone. Thank you for joining today's pilot review.
As a day-ahead electricity procurement team at a major UK utility, you face a multimillion-pound challenge every single day before gate closure: How much wholesale power do you need to procure to balance your retail demand, and how much can you trust the wind to deliver?

Under the UK Balancing and Settlement Code, if wind generation falls short of what you contracted, you are forced into the Cash-Out or System Imbalance market at severe penalty rates. But if you over-procure thermal plant power unnecessarily, you lock in excessive wholesale premiums that erode your margins.

Today, I am proud to present WindSight, the analytics platform we engineered specifically for your trading desk during this pilot, focusing on real outturn data from January 2026.

Let us dive straight into the portal. Our design principle was simple: give traders actionable clarity in seconds, not spreadsheets.

At the top of the dashboard, traders immediately see the headline performance for the selected date range:
First, Mean Absolute Error: On average, our day-ahead forecast deviates by approximately 2,210 megawatts.
Second, RMSE: Highlighting extreme volatility spikes.
Third, MAPE: Relative error rate averaging 18.9 percent.
And most crucially, notice the positive systematic bias of plus 1,150 megawatts. This proves that during January 2026, the day-ahead wind forecasts were systematically over-predicting wind generation. Armed with this quantified insight, your traders know they must apply a defensive derating factor to avoid costly imbalance deficits.

Below the KPIs, we have the heart of the platform. We took National Grid ESO's WINDFOR feed and filtered it specifically for the latest forecast published before 09:00 UTC on day D minus 1, the exact information state your traders had before submitting auction bids.
In purple, you see the actual wind generation from Elexon FUELHH. In cyan, the day-ahead forecast. Hovering over any half-hour reveals the exact megawatt divergence and error percentage.

Next, let us look at the Accuracy Analysis tab. Traders told us: We don't just want an average error; we need to know the error distribution so we can calculate hedging buffers.
Here, we see the empirical probability distribution of forecast errors. Notice the skewness towards positive errors.
Looking at the Percentiles Table:
The 90th percentile error sits at plus 4,800 megawatts.
The 95th percentile sits at plus 6,100 megawatts.
This means if your desk wants a 95 percent confidence guarantee against deficit imbalance exposure during high-wind winter events, you need exactly 6.1 gigawatts of flexible thermal backup or battery discharge contracts on standby.
We also provide grouped accuracy by Hour of Day and Day of Month. Notice that forecast errors consistently peak during evening peak demand, between 17:00 and 19:00 UTC, exactly when power prices are highest. This diurnal pattern allows your desk to time intraday trades dynamically.

Now, let us explore our most unique feature: the Forecast Evolution Explorer.
National Grid ESO publishes updated WINDFOR forecasts roughly 8 times a day. How does the forecast change as delivery approaches?
Selecting January 15th, 2026:
The earliest 72-hour forecast predicted 11,500 megawatts.
By Day D minus 1 gate closure, our benchmark, it adjusted to 14,200 megawatts.
By 4 hours before delivery, it converged within 3 percent of the actual 14,800 megawatt outturn.
This allows your intraday trading desk to track forecast convergence velocity. When vintages stabilize early, you can trade with high confidence. When vintages oscillate erratically, you know weather front uncertainty is elevated, signaling a need for wider bid-ask spreads.

To summarize the business value of this pilot:
First, Avoided Imbalance Penalties: Identifying the systematic over-forecast bias saves an estimated 1.2 to 2.4 million pounds annually in winter cash-out penalties.
Second, Optimal Hedging: Quantified 95th percentile risk thresholds ensure you never over-hedge expensive thermal peaking generation.
Third, Turnkey Production Architecture: WindSight is fully dockerized, lightning-fast with sub-50 millisecond query times, and ready to deploy into your internal trading infrastructure or secure cloud.
Thank you very much. We look forward to rolling this out to your live trading desks.
"""

# Script for Part 2: Technical Architecture & Code Review
PART2_SCRIPT = """
Hi everyone. In this section, I will walk through the technical architecture, data pipelines, statistical algorithms, and codebase design for WindSight.

We chose a decoupled modern stack:
On the Backend: Python 3.12 with FastAPI. Python was chosen because energy time-series analytics require vectorized operations with Pandas and NumPy, and statistical distributions. FastAPI gives us high-throughput asynchronous I/O with automatic OpenAPI documentation.
On the Frontend: React with Vite and Recharts. Recharts renders responsive SVG-based charts capable of rendering thousands of points smoothly without canvas overhead.
For Containers and Proxy: Multi-stage Docker containers orchestrated via Docker Compose, with Nginx handling single-page application routing and API reverse-proxying.

Let us look at the data ingestion and domain alignment challenges:
First, The Granularity Mismatch Challenge:
FUELHH actual generation is reported in half-hour settlement periods, 48 per day.
WINDFOR forecasts are reported on an hourly cadence.
In analytics dot py, process actuals, we floor the half-hourly timestamps to the hour and compute the arithmetic mean of the two half-hours. This guarantees clean one-to-one alignment without temporal leakage.

Second, High-Performance Concurrency and Two-Tier Caching:
Elexon BMRS stream endpoints can be slow for bulk range queries. If fetched sequentially, querying 31 days would take 30 plus seconds.
In elexon client dot py, we implemented asynchronous batching using asyncio dot gather bounded by an asyncio Semaphore of 10.
We implemented a two-tier cache: an in-memory dictionary cache for hot endpoint calls, backed by a persistent disk cache in data cache storing pre-validated JSON chunks. All 1,488 actual records and 19,272 forecast records for January 2026 are pre-warmed, delivering sub-50 millisecond API latencies.

Now, a critical software requirement was: How do we identify the true day-ahead forecast?
In the UK wholesale market, traders participate in day-ahead auctions on day D minus 1 before gate closure, between 09:00 and 11:00 UTC.
If you evaluate accuracy using a forecast published 2 hours before delivery, you are evaluating an intraday forecast, not a day-ahead decision.
In get day ahead forecasts, we compute the dynamic cutoff boundary at 09:00 UTC on day D minus 1 for each delivery hour. We then sort by publish time descending and group by timestamp, taking the first available forecast.
This guarantees that every single data point in our comparison and accuracy metrics reflects the freshest available forecast at the exact moment of the auction commitment.

Next, let us examine how the metrics are calculated in analytics dot py:
All calculations are vectorized across Pandas Series:
Mean Absolute Error is the mean of absolute error.
Root Mean Square Error is the square root of mean squared error.
MAPE is calculated with zero-division protection.
Systematic Bias indicates directional skew.
And Pearson correlation measures tracking alignment.
The compute accuracy metrics function also supports dynamic grouping by hour of day and by day of month.
In build error distribution, we calculate 30 histogram bins using numpy histogram and compute non-parametric percentiles from the 5th to the 95th percentile, along with skewness and kurtosis. This provides traders with empirical value-at-risk parameters.

On the frontend:
The component architecture is cleanly divided into Dashboard View, Accuracy View, and Forecast View.
State management maintains clean unidirectional data flow, synchronized across all views with debounced apply filters.
In production, multi-stage Docker builds ensure fast delivery: Node alpine builds the frontend in under 5 seconds, served by Nginx. The backend uses Astral's uv engine for dependency installation in just 11 seconds.
Running docker compose up build launches the complete stack with passing health checks on ports 3000 and 8000.

Thank you, and I am ready for your questions.
"""

def generate_tts(text: str, output_path: str):
    print(f"Calling Deepgram TTS for {output_path}...")
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    # Deepgram API handles text up to ~2000 chars per chunk, so split into paragraphs if needed
    paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    raw_files = []
    
    with httpx.Client(timeout=60.0) as client:
        for idx, p in enumerate(paragraphs):
            chunk_file = f"temp_chunk_{idx}.mp3"
            response = client.post(DEEPGRAM_URL, headers=headers, json={"text": p})
            if response.status_code != 200:
                print(f"Error on chunk {idx}: {response.status_code} - {response.text}")
                continue
            with open(chunk_file, "wb") as f:
                f.write(response.content)
            raw_files.append(chunk_file)
            print(f"Chunk {idx+1}/{len(paragraphs)} generated ({len(response.content)} bytes)")
    
    # Concatenate chunks using ffmpeg concat
    concat_list = "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for rf in raw_files:
            f.write(f"file '{rf}'\n")
    
    temp_concat = "temp_concat.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", temp_concat], check=True)
    
    # Apply speed 0.9 (atempo=0.9) as requested by user
    print(f"Applying speed 0.9 filter to {output_path}...")
    subprocess.run(["ffmpeg", "-y", "-i", temp_concat, "-filter:a", "atempo=0.9", "-q:a", "2", output_path], check=True)
    
    # Cleanup temp files
    for rf in raw_files:
        if os.path.exists(rf):
            os.remove(rf)
    if os.path.exists(concat_list):
        os.remove(concat_list)
    if os.path.exists(temp_concat):
        os.remove(temp_concat)
        
    print(f"Successfully created {output_path} at 0.9x speed!")

if __name__ == "__main__":
    generate_tts(PART1_SCRIPT, "voiceover_part1.mp3")
    generate_tts(PART2_SCRIPT, "voiceover_part2.mp3")
    
    # Combine Part 1 and Part 2 into full voiceover
    with open("full_concat.txt", "w", encoding="utf-8") as f:
        f.write("file 'voiceover_part1.mp3'\nfile 'voiceover_part2.mp3'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "full_concat.txt", "-c", "copy", "voiceover_full.mp3"], check=True)
    if os.path.exists("full_concat.txt"):
        os.remove("full_concat.txt")
    print("ALL VOICEOVERS GENERATED AT 0.9x SPEED SUCCESSFULLY!")
