# Device Log Intelligence Platform

A FastAPI-based platform that parses Android logcat log files, detects error patterns, classifies severity, extracts device information, and visualizes everything on an interactive dashboard.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What It Does

Android logcat files are raw, unstructured text that is difficult to analyze manually. This platform automates the entire process:

1. Upload a `.log` or `.txt` logcat file
2. The parser extracts every log line into structured data (timestamp, level, tag, message, PID, TID)
3. Error patterns are detected and classified into Critical / High / Medium severity
4. Device information is automatically extracted from log content
5. An interactive dashboard displays charts, stats, and filterable log entries

---

## Features

- **Multi-format Log Parsing** — Supports all common Android logcat formats (detailed YYYY-MM-DD, Android MM-DD, time-only, simple E/Tag)
- **25+ Error Pattern Detection** — FATAL EXCEPTION, ANR, NullPointerException, OutOfMemoryError, SIGSEGV, SIGABRT, Native crash, Permission denied, and more
- **Severity Classification** — Classifies every error into Critical / High / Medium buckets
- **Device Info Extraction** — Automatically extracts device model, manufacturer, Android version, SDK, battery level, kernel version, and build fingerprint
- **Interactive Dashboard** — Charts for log level distribution, top errors, top tags, top messages, and system health score
- **Clickable Stat Cards** — Click any metric card to browse all logs in that category with search and filtering
- **Search in Error Logs** — Real-time search by message or tag within any log view
- **REST API** — Full API with pagination, filtering by level, tag, and message search
- **Dual Database** — PostgreSQL in production, SQLite locally (auto-detected via environment variable)
- **Auto-reset on Refresh** — Dashboard clears all data on page load, ready for a fresh upload

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, Uvicorn |
| Database | PostgreSQL (production) / SQLite (local) |
| Frontend | HTML, Chart.js |
| Deployment | Render + Neon PostgreSQL |

---

## Project Structure

```
Device Log Intelligence Platform/
├── app/
│   ├── main.py                 # FastAPI app, CORS, lifespan, exception handlers
│   ├── routes/
│   │   └── logs.py             # All API endpoints
│   ├── services/
│   │   ├── log_parser.py       # Logcat parsing engine (6 regex formats)
│   │   └── error_detector.py   # Error pattern detection and severity classification
│   ├── models/
│   │   └── log_models.py       # SQLAlchemy models: Log, ErrorSummary, DeviceInfo
│   └── utils/
│       ├── database.py         # DB engine (PostgreSQL / SQLite auto-detection)
│       └── auth.py             # Token-based auth (demo)
├── dashboard/
│   └── index.html              # Full dashboard UI with Chart.js
├── logs/                       # Uploaded log files (auto-created)
├── render.yaml                 # Render deployment config
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/device-log-intelligence-platform.git
cd device-log-intelligence-platform
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run locally

```bash
python -m app.main
```

No environment variables needed — defaults to SQLite automatically.

### 4. Open the dashboard

```
http://localhost:8000/dashboard
```

Interactive API docs available at:
```
http://localhost:8000/docs
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/login` | Get demo auth token |
| `POST` | `/api/upload-log` | Upload and parse a log file |
| `GET` | `/api/summary` | Full analytics summary |
| `GET` | `/api/logs` | Paginated logs with filters |
| `GET` | `/api/logs/by-level` | Logs filtered by level type |
| `DELETE` | `/api/logs` | Delete all logs |

### Upload a log file

```bash
curl -X POST "http://localhost:8000/api/upload-log" \
  -F "file=@/path/to/logcat.log"
```

### Get full summary

```bash
curl http://localhost:8000/api/summary
```

### Get paginated logs with filters

```bash
curl "http://localhost:8000/api/logs?page=1&page_size=50&level=ERROR&search=NullPointer"
```

### Get logs by level type

```bash
# level_type options: errors, warnings, info, debug, verbose, all
curl "http://localhost:8000/api/logs/by-level?level_type=errors&page=1&page_size=100"
```

---

## Supported Log Formats

```
# Detailed (YYYY-MM-DD)
2024-01-15 10:30:45.123  1234  5678 E AndroidRuntime: FATAL EXCEPTION

# Android (MM-DD)
01-15 10:30:45.123  1234  5678 E AndroidRuntime: FATAL EXCEPTION

# Time-only
10:30:45.123  1234  5678 E AndroidRuntime: FATAL EXCEPTION

# Simple
E/AndroidRuntime: FATAL EXCEPTION
```

---

## Detected Error Patterns

`FATAL EXCEPTION` · `ANR` · `NullPointerException` · `OutOfMemoryError` · `StackOverflowError` · `IllegalStateException` · `IllegalArgumentException` · `SecurityException` · `ClassCastException` · `IndexOutOfBoundsException` · `RuntimeException` · `SIGSEGV` · `SIGABRT` · `Native crash` · `Permission denied` · `Connection refused` · `Connection timeout` · `Network unreachable` · `Binder transaction failed` · `Process died` · `Force finishing` · and more

---

## Severity Classification

| Severity | Criteria |
|---|---|
| **Critical** | FATAL level, ANR, OutOfMemoryError, StackOverflowError, SIGSEGV, SIGABRT, Native crash |
| **High** | Any Exception, crash, failed, permission denied |
| **Medium** | All other ERROR level logs |

**Health Score** = `max(0, 100 - (error_count × 0.5) - (warning_count × 0.2))`

---

## Database Schema

```
logs               — id, timestamp, pid, tid, level, tag, message, created_at
error_summary      — id, error_type (unique), count, updated_at
device_info        — id, device_model, manufacturer, android_version, sdk_version,
                     battery_level, battery_health, kernel_version, build_fingerprint, ...
```

---

## Deployment

The app auto-detects its environment via the `DATABASE_URL` environment variable:

- **Locally** — no env var needed, SQLite file created automatically
- **Production** — set `DATABASE_URL` to a PostgreSQL connection string

```bash
export DATABASE_URL=postgresql://user:password@host/dbname
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Production only | PostgreSQL connection string |

---

## License

MIT
