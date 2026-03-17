# 🚀 AI-Based Interview Orchestration & Multi-Node Execution Framework

A **production-grade distributed AI system** designed to conduct, monitor, and evaluate online interviews with **scalability, fault tolerance, and real-time monitoring**.

---

# 📌 Overview

This project implements a **distributed orchestration system** that manages multiple AI-powered interview sessions across worker nodes.

It integrates:

* 🎥 Video Monitoring (Computer Vision)
* 🎙 Audio Processing (Speech-to-Text)
* 🧠 AI Answer Evaluation (LLMs)
* ⚠️ Risk Scoring Engine
* ⚙️ Distributed Task Execution
* 📊 Real-Time Monitoring Dashboard

---

# 🏗️ System Architecture

```
                ┌──────────────────────────┐
                │   FastAPI Orchestrator   │
                │ (Scheduler + LoadBalancer)│
                └────────────┬─────────────┘
                             │
                    Redis Task Queue
                             │
        ┌──────────────┬──────────────┬──────────────┐
        │ Worker Node 1│ Worker Node 2│ Worker Node N│
        └──────┬───────┴──────┬───────┴──────┬───────┘
               │              │              │
     Video + Audio + NLP Processing Pipelines
               │
        PostgreSQL Database
               │
        Monitoring Dashboard (API + WebSocket)
```

---

# ⚙️ Tech Stack

### Backend

* FastAPI (API & Orchestration)
* Celery (Distributed Task Queue)
* Redis (Broker & Cache)
* PostgreSQL (Database)

### AI Modules

* OpenCV / MediaPipe (Video Processing)
* Whisper (Speech-to-Text)
* GPT / LLM (Answer Evaluation)

### DevOps

* Docker (Containerization)
* AWS Ready (Deployment)

---

# 📦 Modules Breakdown

## ✅ Module 1 — System Setup

* Project structure
* FastAPI server
* Redis + PostgreSQL setup

---

## ✅ Module 2 — Distributed Task Queue

* Celery + Redis integration
* Asynchronous task execution
* Parallel processing

---

## ✅ Module 3 — Worker Execution System

* Video, Audio, Evaluation pipelines
* Risk scoring engine
* Worker concurrency

---

## ✅ Module 4 — Session State Management

* Session lifecycle tracking
  `CREATED → QUEUED → PROCESSING → COMPLETED / FAILED`
* Redis caching + PostgreSQL persistence
* Real-time session tracking

---

## ✅ Module 5 — Orchestration & Load Balancing

* Worker Registry (health tracking)
* Load balancing strategies:

  * Round Robin
  * Least Loaded (recommended)
  * Queue-Based
* Intelligent scheduling system

---

## ✅ Module 6 — Fault Tolerance & Recovery

* Retry system with exponential backoff
* Worker failure detection
* Task reassignment
* Dead Letter Queue (DLQ)
* Health monitoring system
* Failure logging & analytics

---

## ✅ Module 7 — Monitoring Dashboard

* Real-time system metrics
* Worker health monitoring
* Session tracking
* Failure & retry analytics
* WebSocket-based live updates

---

# 🔥 Key Features

### 🚀 Scalability

* Horizontal scaling via worker nodes
* Distributed task execution

### ⚡ Performance

* Non-blocking API
* Parallel processing

### 🛡 Fault Tolerance

* Retry mechanisms
* Dead letter queue
* Worker failure recovery

### 📊 Observability

* Real-time dashboard
* System health tracking
* Analytics & monitoring

---

# 📡 API Endpoints

### 🎯 Core

* `POST /start-interview`
* `GET /session-status/{session_id}`

### ⚙️ Worker Management

* `POST /register-worker`
* `POST /worker/heartbeat`
* `GET /workers`

### 📊 Monitoring

* `GET /system-health`
* `GET /worker-health`
* `GET /metrics/*`

### 🔁 Recovery

* `POST /retry-session/{session_id}`
* `GET /failed-sessions`
* `GET /dead-letter-queue`

---

# 📊 Monitoring Dashboard

The system includes a real-time dashboard showing:

* Active sessions
* Worker status
* Queue load
* Failures & retries
* Risk score analytics

---

# 🚀 How to Run

### 1. Install Dependencies

```
pip install -r requirements.txt
```

### 2. Start Services

```
docker-compose up
```

### 3. Run API

```
uvicorn orchestrator.main:app --reload
```

### 4. Open API Docs

```
http://localhost:8000/docs
```

---

# 🧠 Key Concepts Implemented

* Distributed Systems Architecture
* Task Queues & Async Processing
* Load Balancing Algorithms
* Fault Tolerance & Recovery
* Dead Letter Queue Pattern
* Real-Time Monitoring
* System Observability

---

# 📈 Project Highlights

* Built a **fault-tolerant distributed system**
* Implemented **production-level retry logic**
* Designed **scalable multi-node architecture**
* Developed **real-time monitoring dashboard**
* Integrated **AI pipelines with orchestration layer**



---

# 🚀 Future Enhancements

* Kubernetes deployment
* GPU-based worker scaling
* Advanced analytics dashboard
* Real-time alerts & notifications

---
# 👨‍💻 Author

Mukta Redij
