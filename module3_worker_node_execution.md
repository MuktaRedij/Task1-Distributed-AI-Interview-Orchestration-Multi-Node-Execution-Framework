# Module 3 --- Worker Node Execution System

Project: AI Interview Orchestration & Multi-Node Execution Framework

This module implements the worker node execution system responsible for
running AI interview pipelines.

Worker nodes receive tasks from the Redis queue and execute the full AI
interview analysis pipeline.

------------------------------------------------------------------------

# Objective

Implement worker services that execute the AI monitoring pipelines for
interview sessions.

Workers should:

-   process interview sessions
-   run video monitoring
-   run audio monitoring
-   evaluate candidate answers
-   calculate risk scores
-   store results in PostgreSQL

Workers must be scalable and capable of running on multiple nodes.

------------------------------------------------------------------------

# Worker Architecture

Execution flow:

Redis Queue\
→ Celery Worker\
→ Video Pipeline\
→ Audio Pipeline\
→ Answer Evaluation Pipeline\
→ Risk Scoring Engine\
→ Database Storage

Each worker node should be able to process multiple sessions
simultaneously.

------------------------------------------------------------------------

# Files To Implement

Create or expand the following worker modules:

workers/ ├── worker.py ├── tasks.py ├── video_pipeline.py ├──
audio_pipeline.py ├── evaluation_pipeline.py └── risk_engine.py

------------------------------------------------------------------------

# Video Monitoring Pipeline

File: workers/video_pipeline.py

Responsibilities:

-   Face detection
-   Head pose monitoring
-   Mobile phone detection
-   Multiple person detection

Return example output:

{ "face_detected": true, "multiple_people": false, "phone_detected":
false, "head_movement_score": 0.3 }

------------------------------------------------------------------------

# Audio Monitoring Pipeline

File: workers/audio_pipeline.py

Responsibilities:

-   Speech-to-text using Whisper
-   Background voice detection
-   Suspicious conversation detection

Example output:

{ "speech_text": "candidate response", "background_voice_detected":
false, "conversation_risk": 0.2 }

------------------------------------------------------------------------

# Answer Evaluation Pipeline

File: workers/evaluation_pipeline.py

Responsibilities:

-   evaluate candidate answers
-   generate score using LLM
-   generate feedback

Example output:

{ "answer_score": 0.8, "confidence": 0.75 }

------------------------------------------------------------------------

# Risk Scoring Engine

File: workers/risk_engine.py

Combine signals from all pipelines.

Example logic:

risk_score = 0.4 \* video_risk + 0.3 \* audio_risk + 0.3 \*
evaluation_score

Return a final risk value between 0 and 1.

------------------------------------------------------------------------

# Task Execution Flow

File: workers/tasks.py

Primary task:

process_interview_session(session_id)

Execution order:

1.  run video pipeline
2.  run audio pipeline
3.  run answer evaluation
4.  calculate risk score
5.  store results in database
6.  update session status

------------------------------------------------------------------------

# Worker Scalability

Workers should support parallel execution.

Example command:

celery -A workers.celery_app worker --loglevel=info --concurrency=4

This allows one worker node to process multiple sessions simultaneously.

Multiple worker nodes can be deployed to increase system capacity.

------------------------------------------------------------------------

# Database Update

After processing a session:

Update the InterviewSession record with:

status = "completed" risk_score = calculated score end_time = timestamp

------------------------------------------------------------------------

# Expected Output

After implementing this module the system should:

-   run AI pipelines inside worker nodes
-   process interview sessions asynchronously
-   calculate risk scores
-   store results in database
-   support distributed execution

------------------------------------------------------------------------

# Next Module

Module 4 --- Session State Management

This module will implement:

-   session lifecycle tracking
-   distributed state synchronization
-   session recovery
-   session timeout handling
