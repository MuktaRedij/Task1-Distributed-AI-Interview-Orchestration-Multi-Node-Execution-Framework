# Module 2 --- Distributed Task Queue (Redis + Celery)

**Project:** AI Interview Orchestration & Multi-Node Execution
Framework\
**Module Goal:** Implement a distributed task processing system using
**Celery + Redis** to enable parallel execution of interview pipelines
across multiple worker nodes.

------------------------------------------------------------------------

# Objective

Create a distributed execution layer that allows multiple AI interview
sessions to run simultaneously across multiple compute nodes.

This module will implement:

-   Celery task queue
-   Redis message broker
-   Worker node execution system
-   Distributed task processing
-   Integration with the orchestration layer

This module enables **horizontal scalability and parallel AI pipeline
execution**.

------------------------------------------------------------------------

# System Architecture

## Execution Flow

Candidate Interview Request\
→ FastAPI Orchestrator\
→ Redis Task Queue\
→ Celery Worker Nodes\
→ AI Processing Pipelines\
→ Results stored in PostgreSQL

Workers pull tasks from the Redis queue and execute AI pipelines.

------------------------------------------------------------------------

# Technologies

  Component        Technology
  ---------------- ------------
  Task Queue       Celery
  Message Broker   Redis
  Workers          Python
  Backend API      FastAPI
  Database         PostgreSQL

------------------------------------------------------------------------

# Files To Implement

Add the following files in the project:

workers/ ├── celery_app.py ├── worker.py ├── tasks.py ├──
video_pipeline.py ├── audio_pipeline.py └── evaluation_pipeline.py

------------------------------------------------------------------------

# Celery Application Setup

Create `workers/celery_app.py`.

This file initializes Celery and connects to Redis.

## Responsibilities

-   Configure Redis as broker
-   Configure Redis as result backend
-   Define task serialization
-   Load task modules

## Example Implementation

``` python
from celery import Celery
from config import REDIS_URL

celery_app = Celery(
    "interview_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json"
)

celery_app.autodiscover_tasks(["workers"])
```

------------------------------------------------------------------------

# Worker Node Initialization

Create `workers/worker.py`.

This file starts the Celery worker service.

The worker should listen for tasks from the Redis queue and process
interview sessions.

## Example Run Command

``` bash
celery -A workers.celery_app worker --loglevel=info --concurrency=4
```

Worker nodes can be deployed across multiple machines to scale interview
processing.

------------------------------------------------------------------------

# Task Implementation

Create `workers/tasks.py`.

Define Celery tasks responsible for executing interview pipelines.

## Primary Task

``` python
process_interview_session(session_id)
```

## Task Responsibilities

1.  Start video monitoring pipeline
2.  Start audio monitoring pipeline
3.  Run answer evaluation
4.  Calculate final risk score
5.  Store results in database

## Example Task Structure

``` python
from workers.celery_app import celery_app

@celery_app.task
def process_interview_session(session_id):

    video_result = run_video_analysis(session_id)

    audio_result = run_audio_analysis(session_id)

    evaluation = evaluate_answers(session_id)

    risk_score = calculate_risk(video_result, audio_result)

    return risk_score
```

------------------------------------------------------------------------

# AI Pipeline Modules

Create the following modules.

## video_pipeline.py

Handles computer vision tasks.

### Responsibilities

-   Face detection
-   Head movement detection
-   Mobile phone detection
-   Multiple person detection

------------------------------------------------------------------------

## audio_pipeline.py

Handles speech monitoring.

### Responsibilities

-   Speech-to-text using Whisper
-   Background voice detection
-   Suspicious conversation detection

------------------------------------------------------------------------

## evaluation_pipeline.py

Handles answer evaluation.

### Responsibilities

-   LLM answer evaluation
-   Score generation
-   Feedback generation

These modules will be called by Celery tasks.

------------------------------------------------------------------------

# FastAPI Integration

Modify the orchestrator API so that interview sessions are pushed into
the Redis task queue.

## Example

``` python
from workers.tasks import process_interview_session

@app.post("/start-interview")
def start_interview(session_id):

    process_interview_session.delay(session_id)

    return {"message": "Interview session queued"}
```

This allows the API server to **enqueue interview tasks without blocking
execution**.

------------------------------------------------------------------------

# Testing the Distributed Queue

## Start Redis

``` bash
docker-compose up redis
```

## Start Celery Workers

``` bash
celery -A workers.celery_app worker --loglevel=info
```

## Start FastAPI Server

``` bash
uvicorn orchestrator.main:app --reload
```

## Trigger Interview Session

Send a request to the API endpoint.

Workers should automatically pick up the task from Redis.

------------------------------------------------------------------------

# Expected Output of Module 2

After completing this module, the system should support:

-   Distributed interview processing
-   Redis-based task queue
-   Celery worker nodes
-   Parallel AI pipeline execution
-   Non-blocking API task submission

This module enables **scalable interview orchestration**.

------------------------------------------------------------------------

# Next Module

## Module 3 --- Worker Node Execution System

This module will implement:

-   Full AI pipeline execution inside worker nodes
-   Resource management
-   GPU/CPU workload balancing
-   Worker health monitoring
S