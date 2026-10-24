# WindSight ⚡ Client Pitch & Pilot Presentation (Part 1)

> **Audience**: Power Procurement & Trading Team, UK Energy Utility  
> **Speaker**: Lead Full-Stack Product Developer  
> **Duration**: ~4 to 5 minutes  
> **Goal**: Impress the client with the pilot portal, demonstrate clear financial and operational value for their day-ahead trading workflow, and present actionable January 2026 insights.

---

## ⏱️ Video Script & Slide Breakdown (0:00 – 4:45)

### Minute 0:00 – 0:45: The Hook & Client Problem Setting
**[Visual: Title Slide / Dashboard View loading instantly]**

> *"Good morning, everyone. Thank you for joining today's pilot review.*  
> *As a day-ahead electricity procurement team at a major UK utility, you face a multimillion-pound challenge every single day before gate closure: **How much wholesale power do you need to procure to balance your retail demand, and how much can you trust the wind to deliver?***  
>
> *Under the UK Balancing and Settlement Code, if wind generation falls short of what you contracted, you're forced into the Cash-Out / System Imbalance market at severe penalty rates. But if you over-procure thermal or peaker plant power unnecessarily, you lock in excessive wholesale premiums that erode your margins.*  
>
> *Today, I am proud to present **WindSight**—the analytics platform we engineered specifically for your trading desk during this pilot, focusing on real outturn data from **January 2026**."*

---

### Minute 0:45 – 1:45: Portal Walkthrough — Live Day-Ahead Decision Support
**[Visual: Navigate to the Dashboard View at `http://localhost:3000` / Live App]**

> *"Let’s dive straight into the portal.*  
> *Our design principle was simple: **give traders actionable clarity in seconds, not spreadsheets.**"  
>
> **1. Executive KPI Cards:**  
> *"At the top of the dashboard, traders immediately see the headline performance for the selected date range:  
> - **Mean Absolute Error (MAE)**: On average, our day-ahead forecast deviates by ~2,200 MW.  
> - **RMSE**: Highlighting extreme volatility spikes.  
> - **MAPE**: Relative error rate averaging ~19%.  
> - **Systematic Bias**: Crucially, notice the positive bias of +1,150 MW. This proves that during January 2026, the day-ahead wind forecasts were systematically **over-predicting** wind generation! Armed with this quantified insight, your traders know they must apply a defensive derating factor to avoid costly imbalance deficits.*  
>
> **2. Actual vs. Day-Ahead Forecast Interactive Comparison Chart:**  
> *"Below the KPIs, we have the heart of the platform. We took National Grid ESO's `WINDFOR` feed and filtered it specifically for the latest forecast published **before 09:00 UTC on day D-1**—the exact information state your traders had before submitting auction bids.*  
> *In purple, you see the actual wind generation from Elexon `FUELHH`. In cyan, the day-ahead forecast. Hovering over any half-hour reveals the exact MW divergence and error percentage."*

---

### Minute 1:45 – 2:45: Accuracy Analysis — Quantifying the Error Margin
**[Visual: Switch to Accuracy Analysis View]**

> *"Next, let’s look at the **Accuracy Analysis** tab. Traders told us: 'We don't just want an average error; we need to know the error distribution so we can calculate hedging buffers.'*  
>
> **1. Error Distribution Histogram & Percentiles:**  
> *"Here, we see the empirical probability distribution of forecast errors. Notice the skewness towards positive errors.  
> Looking at the **Percentiles Table**:  
> - The 90th percentile error sits at +4,800 MW.  
> - The 95th percentile sits at +6,100 MW.  
> This means if your desk wants a 95% confidence guarantee against deficit imbalance exposure during high-wind winter events, you need exactly 6.1 GW of flexible thermal backup or battery discharge contracts on standby."*  
>
> **2. Diurnal & Time Breakdown:**  
> *"We also provide grouped accuracy by **Hour of Day** and **Day of Month**. Notice that forecast errors consistently peak during evening peak demand (17:00–19:00 UTC)—exactly when power prices are highest! This diurnal pattern allows your desk to time intraday trades dynamically."*

---

### Minute 2:45 – 3:45: Forecast Evolution — The Multi-Vintage Advantage
**[Visual: Switch to Forecast Explorer View]**

> *"Now, let's explore our most unique feature: **Forecast Evolution Explorer**.*  
> *National Grid ESO publishes updated `WINDFOR` forecasts roughly 8 times a day. How does the forecast change as delivery approaches?*  
>
> *Selecting **January 15th, 2026**:  
> - The earliest 72-hour forecast predicted 11,500 MW.  
> - By Day D-1 gate closure (our benchmark), it adjusted to 14,200 MW.  
> - By 4 hours before delivery, it converged within 3% of the actual 14,800 MW outturn.*  
>
> *This allows your intraday trading desk to track **forecast convergence velocity**. When vintages stabilize early, you can trade with high confidence. When vintages oscillate erratically, you know weather front uncertainty is elevated, signaling a need for wider bid-ask spreads."*

---

### Minute 3:45 – 4:45: Business Value, ROI & Next Steps
**[Visual: Summary Slide or Full Dashboard Overview]**

> *"To summarize the business value of this pilot:  
> 1. **Avoided Imbalance Penalties**: Identifying the systematic over-forecast bias saves estimated £1.2M–£2.4M annually in winter cash-out penalties.  
> 2. **Optimal Hedging**: Quantified 95th percentile risk thresholds ensure you never over-hedge expensive thermal peaking generation.  
> 3. **Turnkey Production Architecture**: WindSight is fully dockerized, lightning-fast with sub-50ms query times, and ready to deploy into your internal trading infrastructure or secure cloud.*  
>
> *Thank you very much. We look forward to rolling this out to your live trading desks!"*

---

## 🎯 Key Questions the Client May Ask & Answers

1. **Q: Where does the data come from?**  
   *A: 100% official Elexon BMRS APIs—specifically `FUELHH/stream` for actual generation by fuel type (WIND) and `WINDFOR/stream` for wind generation forecasts.*

2. **Q: How do you handle daylight savings or timezone differences?**  
   *A: All timestamps are processed in UTC (ISO-8601), matching the UK electricity settlement standard across all 48 half-hour settlement periods.*

3. **Q: Can this be connected to our internal private forecasts?**  
   *A: Yes. The analytics engine is completely modular and accepts any standardized forecast pandas DataFrame or REST endpoint.*
