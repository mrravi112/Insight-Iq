# 🚀 InsightIQ – AI-Powered Data Intelligence Platform

### Turn Raw Data into Meaningful Insights. Make Smarter Decisions.

**InsightIQ** is an AI-powered data intelligence platform designed to simplify data analysis and transform complex datasets into meaningful, actionable insights.

By combining automated data processing, statistical analysis, interactive visualizations, and AI-driven interpretations, InsightIQ helps users understand their data without spending hours manually exploring spreadsheets and raw datasets.

Whether you're analyzing trends, identifying patterns, exploring statistical relationships, or generating analytical reports, InsightIQ brings everything together in one intelligent workspace.

---

## 🌟 Overview

Data is everywhere, but extracting meaningful information from it can be challenging.

InsightIQ bridges the gap between raw data and informed decision-making through an intelligent analytics workflow.

Users can upload datasets, explore statistical information, visualize patterns, and receive AI-powered explanations that make analytical results easier to understand.

**Our Vision:** Make advanced data analytics accessible, intuitive, and intelligent for everyone.

---

## ✨ Key Features

### 📊 Automated Data Analysis
- Process and analyze uploaded datasets.
- Automatically identify important columns and data patterns.
- Generate meaningful analytical summaries.
- Explore datasets without extensive manual processing.

### 📈 Statistical Exploration
- Calculate essential statistical measures.
- Understand data distributions and variations.
- Identify trends, relationships, and potential anomalies.
- Explore numerical patterns through statistical analysis.

### 🎨 Interactive Data Visualization
- Convert complex numerical information into visual insights.
- Explore datasets through graphical representations.
- Understand relationships and trends more effectively.
- Make analytical findings easier to interpret.

### 🤖 AI-Powered Insights
- Generate natural-language interpretations of analytical results.
- Explain important patterns discovered in datasets.
- Convert statistical findings into understandable explanations.
- Support data-driven decision-making through intelligent analysis.

### 📁 Intelligent Data Processing
- Work with raw datasets through an organized workflow.
- Handle dataset ingestion and preprocessing.
- Prepare structured data for further analysis.
- Simplify the overall data exploration process.

### 📝 Intelligent Reporting
- Present analytical findings in a structured format.
- Generate understandable summaries of important metrics.
- Organize insights for easier interpretation and reporting.

### 🔐 Privacy-Aware Architecture
- Incorporate privacy-conscious data handling.
- Separate data processing and analytical operations.
- Apply privacy-focused practices throughout the analysis workflow.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React.js, TypeScript, Vite |
| Styling | CSS |
| Backend | Python, FastAPI |
| API Communication | REST API |
| Analytics | Statistical Analysis, Data Processing |
| Intelligence | NLP-Based Analysis |
| Visualization | Data Visualization |
| Testing | Python Testing Framework |

---

## 🏗️ Project Architecture

InsightIQ follows a modular architecture that separates frontend presentation, backend processing, and analytical operations.

```text
                  ┌──────────────────────┐
                  │        USER          │
                  │   Uploads Dataset    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   REACT FRONTEND     │
                  │  TypeScript + Vite   │
                  └──────────┬───────────┘
                             │
                          REST API
                             │
                             ▼
                  ┌──────────────────────┐
                  │    FASTAPI BACKEND   │
                  └──────────┬───────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │   Data   │   │ Statistical│  │   NLP    │
        │ Ingestion│   │ Analytics  │  │ Analysis │
        └──────────┘   └──────────┘   └──────────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                  ┌──────────────────────┐
                  │   INSIGHTS & REPORTS │
                  │ Visualizations + AI  │
                  └──────────────────────┘
```

---

## 📂 Project Structure

```text
Insight-Iq/
│
├── backend/
│   ├── app/
│   │   ├── analytics.py       # Statistical analysis
│   │   ├── config.py          # Application configuration
│   │   ├── db.py              # Database operations
│   │   ├── ingest.py          # Dataset ingestion
│   │   ├── main.py            # FastAPI entry point
│   │   ├── nlp.py             # NLP-based intelligence
│   │   ├── privacy.py         # Privacy-related operations
│   │   └── reports.py         # Analytical report generation
│   │
│   ├── tests/                 # Backend test cases
│   └── requirements.txt       # Python dependencies
│
├── frontend/
│   ├── src/                   # React application source
│   ├── package.json           # Frontend dependencies
│   └── vite.config.ts         # Vite configuration
│
├── sample_data/               # Sample datasets
│
├── run_backend.bat            # Backend startup script
├── run_frontend.bat           # Frontend startup script
├── start_all.bat              # Start complete application
│
├── .gitignore
└── README.md
```

---

## ⚙️ Installation & Setup

Follow these steps to run InsightIQ locally.

### Prerequisites

Make sure the following tools are installed:

- Python 3.10+
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/mrravi112/Insight-Iq.git

cd Insight-Iq
```

### 2. Backend Configuration

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables using the provided `.env.example` file.

Start the backend using the project's configured startup command.

### 3. Frontend Configuration

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL displayed in your terminal to access the application.

### 4. Run the Complete Application (Windows)

Alternatively, use the provided startup script:

```bash
start_all.bat
```

This script simplifies launching the frontend and backend together.

---

## 🌐 Production Deployment Guide

InsightIQ is architected for dual-cloud deployment: **FastAPI backend on Render** and **React frontend on Vercel**.

### 1. Backend Deployment (Render)

1. Sign in to [Render](https://render.com) and click **New +** → **Web Service**.
2. Connect your GitHub repository (`mrravi112/Insight-Iq`).
3. Set the service configuration:
   - **Name**: `insight-iq`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables under **Settings** → **Environment**:
   - `PYTHON_VERSION`: `3.12.8`
   - `SENTIMENT_BACKEND`: `vader`
   - `CORS_ORIGINS`: `https://insight-iq-smoky.vercel.app,http://localhost:5173`
   - `MAX_UPLOAD_MB`: `25`
   - `MAX_RECORDS`: `50000`
5. Click **Deploy Web Service**.

> **Note on Storage & Sleep Mode**:
> Render free-tier instances sleep after 15 minutes of inactivity; the initial request after idling takes 45–60 seconds to spin up. SQLite data is stored in `backend/data/insightiq.db`. For persistent multi-instance production, set `DATABASE_URL` to a PostgreSQL instance URL (such as a Render Postgres database) and mount a Render Disk for `DATA_DIR`.

### 2. Frontend Deployment (Vercel)

1. Sign in to [Vercel](https://vercel.com) and click **Add New** → **Project**.
2. Import your GitHub repository (`mrravi112/Insight-Iq`).
3. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `frontend`.
4. Add Environment Variables under **Settings** → **Environment Variables**:
   - `VITE_API_URL`: `https://insight-iq-2zkg.onrender.com` *(without trailing slash)*
5. Click **Deploy**.

> **Automatic Proxy & Fallback**:
> `frontend/vercel.json` automatically routes `/api/*` requests to the Render backend and handles SPA client-side routing on page refreshes (`/upload`, `/explorer`, etc.).

---

## 🖥️ Application Preview

Screenshots of the platform will be added here.

| Dashboard | Data Analysis |
|---|---|
| Coming Soon | Coming Soon |

| Visualizations | AI Insights |
|---|---|
| Coming Soon | Coming Soon |

---

## 🎯 Project Objectives

InsightIQ aims to:

- Reduce the complexity of manual data analysis.
- Make statistical exploration more accessible.
- Transform raw datasets into understandable visual insights.
- Use AI to explain analytical findings in natural language.
- Improve the way users explore and interpret information.
- Support smarter, data-driven decision-making.

---

## 🔮 Future Enhancements

Potential improvements for the platform include:

- [ ] Support for additional dataset formats.
- [ ] Advanced predictive analytics.
- [ ] AI-powered natural-language data querying.
- [ ] Automated anomaly detection.
- [ ] Customizable analytical dashboards.
- [ ] Exportable PDF and Excel reports.
- [ ] Advanced data visualization options.
- [ ] Real-time data analysis.

---

## 🤝 Contributing

Contributions, suggestions, and feedback are welcome!

If you would like to improve InsightIQ:

1. Fork the repository.
2. Create a new feature branch.
3. Commit your changes.
4. Push the branch to your fork.
5. Submit a Pull Request.

---

## 👨‍💻 Developers

### Rattanesh Guleria & Ravi

| Developer | GitHub Profile |
|---|---|
| **Rattanesh Guleria** | [@rattaneshguleria](https://github.com/rattaneshguleria) |
| **Ravi** | [@mrravi112](https://github.com/mrravi112) |

---

<div align="center">

### 💡 InsightIQ
**Less Manual Analysis. More Meaningful Insights.**

*Turning Data into Intelligence.*

**Built with ❤️ by Rattanesh Guleria & Ravi**

</div>

## 📄 License

This project is available for educational and development purposes. Add an appropriate open-source license to the repository if you intend to distribute it under specific licensing terms.

---

<div align="center">

# 💡 InsightIQ

### Less Manual Analysis. More Meaningful Insights.

*Turning Data into Intelligence.*

⭐ If you find this project interesting, consider giving the repository a star!

**Built with ❤️ by Rattanesh Guleria & Ravi**

</div>
