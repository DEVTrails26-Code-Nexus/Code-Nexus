## Inspiration

India has over **8 million platform-based gig delivery workers** — the invisible backbone of the Q-commerce economy. Every monsoon season, a Blinkit or Zepto rider like Ravi loses ₹4,000–₹6,000 in income from rain days alone. He can't work, orders don't come, and there is **no safety net whatsoever**.

We were inspired by a simple, infuriating truth: parametric insurance — insurance that pays out automatically when a predefined event occurs — already exists and works. The problem is that every existing platform verifies workers using **GPS alone**. And GPS is software. It can be faked in seconds with a free Android app.

We asked ourselves: *what would it take to build a parametric insurance system that is genuinely fraud-resistant, genuinely instant, and genuinely affordable for a worker earning ₹1,000 a day?* That question became Nexurance AI.

---

## What it does

**Nexurance AI** is an AI-powered insurance verification platform that provides **automatic, zero-touch income protection** for Q-commerce delivery workers against external disruptions — heavy rain, AQI spikes, curfews, and civic shutdowns.

**How it works in 5 steps:**

1. **Onboard (3 minutes):** Worker downloads the Flutter app, signs in via Firebase phone OTP, links UPI ID. Risk profile is assigned automatically.
2. **Subscribe (weekly):** AI calculates a personalised weekly premium (₹15–₹60) based on zone flood risk, weather forecast, and the worker's trust score.
3. **Disruption fires:** A Red Rain Alert triggers in the worker's zone.
4. **Auto-verify (30 seconds):** Our Multi-Signal Trust Scoring (MSTS) engine cross-checks 5 independent physical evidence streams — cell tower triangulation, motion sensors, barometric pressure, network authenticity, and behavioural history.
5. **Payout (< 60 seconds):** ₹480 credited to the worker's UPI. FCM push notification fires instantly. No claim form. No investigator. No waiting.

**Key differentiator — the MSTS fraud engine:**

Traditional platforms trust GPS. We don't. Our MSTS engine computes a trust score (0.0–1.0) by fusing:
- **Location Consistency** — cell tower BTS attachment, WiFi AP fingerprinting, GPS drift physics
- **Motion Validity** — accelerometer FFT patterns, barometric pressure drop matching rain events, gyroscope signatures
- **Network Authenticity** — VPN/proxy ASN detection, Android `Location.isMock()` API, Google Play Integrity attestation
- **Behavioural History** — 90-day rolling zone familiarity, claim frequency baseline, earnings alignment
- **Cluster Isolation** — Louvain community detection on claim submission graphs to catch coordinated fraud rings

Score ≥ 0.80 → instant payout. Score < 0.40 → blocked. Scores in between → tiered review with a Network Forgiveness Buffer for workers who lose signal in genuine rain events.

---

## How we built it

**Mobile App:** Flutter (Android-first) — chosen specifically because `sensors_plus` and `barometer` Flutter plugins give direct, stable access to the accelerometer, gyroscope, and atmospheric pressure sensors that power our fraud engine. FlutterFire connects natively to Firebase with zero bridging overhead.

**Backend API:** FastAPI (Python) — one language for both the API layer and the ML models eliminates the Node↔Python microservice bridge. All business logic, trigger evaluation, and payout routing live here.

**AI/ML Layer — three adaptive models:**
- *Module 1: Dynamic Premium Engine* — XGBoost regression on 8 features (zone flood risk, 7-day weather forecast, AQI, day-of-week, worker history, trust score). Retrains every Sunday night.
- *Module 2: MSTS Fraud Engine* — Isolation Forest anomaly detection + Louvain graph clustering for ring detection. Includes temporal drift detection: if a zone's claim rate deviates >2.5σ from baseline, fraud thresholds auto-tighten without human intervention.
- *Module 3: Payout Eligibility Scorer* — Logistic Regression (interpretable for regulatory compliance). Outputs approve / hold / block.

**Data:**
- Firebase Firestore — real-time policy and claim records with live listeners (worker app updates instantly on payout)
- MongoDB Atlas — unstructured sensor telemetry payloads and fraud graph data (Firestore's query limits would break here)

**Payments:** Razorpay Payout API sandbox — Flutter SDK, UPI + IMPS, sub-60-second settlement.

**Triggers:** OpenWeatherMap API (rainfall), CPCB API (AQI), IMD RSS feed (flood/heat alerts). Platform signals (order density) are used as supporting evidence only — never the sole trigger, eliminating the entire class of platform-manipulation attacks.

**Admin Dashboard:** React + Tailwind — insurer-facing portal with loss ratio charts, fraud ring radar (Louvain cluster visualisation), predictive loss calendar, and zone risk heatmap.

---

## Challenges we ran into

**1. The GPS trust problem.** Every time we designed a verification layer, we asked: "can a rooted Android phone fake this?" GPS — yes. Cell tower attachment — no (network-side record). Barometric pressure reading on a stock device — no (requires physical sensor). Play Integrity attestation — no (cryptographically signed by Google). Building a system where *every single signal* is either server-side verifiable or requires physical presence took significant architectural iteration.

**2. Coordinated fraud rings vs individual fraud.** Detecting one GPS spoofer is a solved problem. Detecting 500 coordinated spoofers who submit simultaneously via a Telegram bot is not. We had to design the Louvain graph clustering layer from scratch — building claim event graphs in real time, applying community detection, and defining statistical thresholds (burst < 8 minutes, cluster > 15 workers, zone spread < 1.5 km) that catch rings without false-positiving on genuine mass disruption events like a city-wide flood.

**3. The honest worker UX problem.** Heavy rain kills 4G signal. A genuine worker in a red-alert zone frequently has no connectivity. Our first draft penalised missing telemetry data — which would have blocked the exact people we're trying to protect. We inverted this: a network drop during a confirmed rain event is *evidence of authenticity*, not a red flag. The Network Forgiveness Buffer adds +0.08 to the trust score in this case.

**4. Actuarial viability.** Building a product that pays out generously in monsoon season while remaining solvent year-round required careful cross-seasonal pooling. Our blended annual loss ratio of ~58% is achievable through monsoon surge pricing (₹40–60/week, 65% loss ratio) offset by dry-season premiums (₹15–25/week, 18% loss ratio). Getting this math to work without external subsidy was a real constraint.

---

## Accomplishments that we're proud of

- **The Network Drop Grace Buffer** — realising that a connectivity loss during a verified rain event is a green flag, not a red flag, is the kind of counterintuitive insight that separates a real product from a prototype.

- **Louvain graph clustering for coordinated fraud** — most fraud detection systems think per-claim. We think per-graph. Detecting a 500-person Telegram-coordinated ring in real time, before payouts drain, is the core technical achievement we're most proud of.

- **The MSTS formula** — a weighted trust score across 5 independently verifiable physical signals, where no single signal can be faked without physical presence, is a genuinely novel verification architecture for the insurance domain.

- **The temporal drift detector** — automatically tightening fraud thresholds when a zone's claim rate deviates >2.5σ from its historical baseline, without any human intervention, means the system gets harder to exploit precisely when attackers think they've found a window.

- **Actuarial sustainability without subsidy** — we proved on paper (and in our model) that this product is viable at scale with a blended 58% loss ratio, within the 55–70% parametric insurance benchmark.

---

## What we learned

- **Verification architecture is the product.** In parametric insurance, the payout logic is straightforward. The hard problem — the one that determines whether your product survives — is the verification layer. We spent more design hours on MSTS than on everything else combined.

- **Gig workers are mobile-first, low-bandwidth, low-trust-of-apps users.** Every design decision has to pass the "would Ravi actually use this?" test. The onboarding has to be under 3 minutes. The premium has to feel like a utility bill, not an insurance contract. The payout notification has to feel like getting a bank transfer, not filing a claim.

- **Coordinated fraud is a systems design problem, not a ML problem.** No single model catches a well-organised Telegram fraud ring. You need graph theory, temporal statistics, and device attestation working together. The insight that real workers' submission times follow a Poisson distribution while coordinated attackers produce a synchronised burst was the breakthrough moment for our fraud engine design.

- **Flutter over React Native for sensor-heavy apps.** The `sensors_plus` and `barometer` plugin ecosystem in Flutter is mature and stable. We would have spent days fighting native bridges in React Native to get the same sensor access that FlutterFire gives us natively.

---

## What's next for Nexurance AI

**Phase 2 (April 4):** Functional Flutter app with Firebase Auth, Firestore real-time policies, FastAPI trigger engine connected to live weather/AQI APIs, and Razorpay sandbox payout flow. Workers can actually subscribe and receive simulated payouts.

**Phase 3 (April 17):** Full MSTS fraud engine with sensor pipeline, Louvain clustering, and temporal drift detection live. Admin insurer dashboard with predictive loss calendar. End-to-end demo: simulated rainstorm → MSTS verification → auto-payout → FCM alert in under 60 seconds.

**Post-hackathon:** Pilot with 500 real Blinkit riders in Bengaluru South Zone. Real premium collection. Real payouts. Real data to retrain our XGBoost and fraud models.

**Year 1:** 2 lakh subscribers across Bengaluru, Mumbai, and Chennai. All three Q-commerce platforms (Zepto, Blinkit, Instamart).

**Year 2:** Expand to food delivery (Zomato, Swiggy). The MSTS engine transfers directly — only the trigger parameters and zone maps change.

**Year 3:** Open the trigger engine as an API platform. Other insurers can build parametric products on our verification infrastructure. Nexurance AI becomes the trust layer for the entire gig economy insurance market.
