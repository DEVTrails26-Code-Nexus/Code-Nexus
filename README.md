# Nexurance AI 🛡️

**A Micro-Parametric Income Protection Platform for Gig Workers**

Developed for **Guidewire DEVTrails 2026** by Team **Code Nexus**.

![Admin Dashboard] (admin_dashboard/public/cover.png) 

Nexurance AI provides instant, claimless income protection for delivery and ride-hailing gig workers who lose earnings due to extreme weather, severe air quality drops, or localized civic disruptions.

---

## 🌟 Core Features

1. **Parametric Triggers**: Automated payouts connected directly to the **OpenWeatherMap** (rainfall) and **OpenAQ** (air quality) APIs. No claims adjuster needed.
2. **MSTS Fraud Engine**: A sophisticated Multi-Signal Trust System that calculates a trust score (0.0 to 1.0) using 5 dimensions:
   - **Location Consistency (L)**: Cell tower matching, WiFi fingerprinting, GPS drift checks.
   - **Motion Validity (M)**: Accelerometer/Gyroscope physics and barometer drops (heavy rain correlates with low atmospheric pressure).
   - **Network Authenticity (N)**: VPN detection, Mock Location checking, and Device Integrity verification.
   - **Behavioural History (B)**: Analysis of past earnings, claim frequency, and zone familiarity.
   - **Cluster Isolation (C)**: Real-time **Louvain Graph Clustering** via NetworkX to detect coordinated fraud rings.
3. **Admin Dashboard**: A React-based control center to monitor real-time weather triggers, view worker trust scores, and simulate rainstorms for live demonstrations.
4. **Worker App**: A Flutter mobile application (runs on Web, Android, iOS) where workers can subscribe to policies, monitor live zone safety data, and receive instant UPI payouts.

---

## 🛠️ Technology Stack

* **Backend Engine**: Python, FastAPI, Motor (Async MongoDB), NetworkX (AI clustering), Uvicorn.
* **Control Center (Web)**: React, Vite, Tailwind CSS, Recharts, Lucide Icons.
* **Mobile App (Gig Worker)**: Flutter, Provider, Dart.
* **Database**: MongoDB (with an in-memory fallback mode for quick hacking).
* **Payment Gateway**: Razorpay (Sandbox) for automated UPI push payouts.

---

## 🚀 Running the Project Locally

The project is split into three main components. You need three separate terminals.

### 1. The AI Backend (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # On Windows
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
*Runs at http://localhost:8000*

### 2. The Admin Control Center (React)
```bash
cd admin_dashboard
npm install
npm run dev
```
*Runs at http://localhost:3000*

### 3. The Gig Worker App (Flutter)
```bash
cd flutter_app
flutter pub get
flutter run -d chrome --web-port 8080
```
*Runs at http://localhost:8080*

---

## 💻 Hackathon Demo flow

For the easiest live presentation experience, the platform includes a built-in simulation engine.

1. Ensure **`DEMO_MODE=true`** is set in `backend/.env`.
2. Open the **Worker App** (`localhost:8080`), click the **"⚡ Demo Login (Ravi Kumar)"** button. View the active policy and trust score.
3. Open the **Admin Dashboard** (`localhost:3000`). Click the **"⚡ Simulate Rainstorm"** button in the top right.
4. The backend will instantly override the weather in Koramangala with 75mm/hr rain, evaluate the MSTS trust score, and process the claim.
5. In the Worker App, go to the **Claims** tab and pull-down-to-refresh to see the instant payout successfully credited!

---

## 🔑 Environment Variables
You need a `.env` file in the `backend/` directory with:
```env
FIREBASE_PROJECT_ID=nexurance-ai
FIREBASE_SERVICE_ACCOUNT_KEY=./nexurance-ai-firebase-adminsdk.json
MONGODB_URI=mongodb://localhost:27017/nexurance_ai
OPENWEATHER_API_KEY=your_key_here
OPENAQ_API_KEY=your_key_here
DEMO_MODE=true
```

## ⚖️ License
Built for the Guidewire DEVTrails Hackathon.
