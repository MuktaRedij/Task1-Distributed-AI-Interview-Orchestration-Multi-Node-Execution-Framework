# Module 4 --- Session State Management & Synchronization

Project: AI Interview Orchestration & Multi-Node Execution Framework

This module implements a robust **session lifecycle management system**
for distributed interview execution.

The goal is to ensure that every interview session is:

-   correctly tracked
-   synchronized across distributed components
-   recoverable in case of failure
-   consistent across API, workers, and database

------------------------------------------------------------------------

# Objective

Design and implement a **Session State Manager** that:

-   tracks the lifecycle of interview sessions
-   ensures state consistency across distributed nodes
-   handles session recovery and failure cases
-   provides real-time session status tracking

------------------------------------------------------------------------

# Session Lifecycle

Each interview session must follow a defined state flow:

CREATED\
→ QUEUED\
→ PROCESSING\
→ COMPLETED\
→ FAILED

Optional intermediate states:

VIDEO_PROCESSING\
AUDIO_PROCESSING\
EVALUATING

------------------------------------------------------------------------

# Files To Implement

Create or update the following:

orchestrator/ ├── session_manager.py ├── state_sync.py └──
session_tracker.py

------------------------------------------------------------------------

# Session Manager

File: orchestrator/session_manager.py

Responsibilities:

-   Create new interview session
-   Update session state
-   Retrieve session details
-   Handle session transitions

Example functions:

create_session(candidate_id)\
update_session_status(session_id, status)\
get_session(session_id)\
mark_session_failed(session_id, error)

Ensure all updates are stored in PostgreSQL.

------------------------------------------------------------------------

# State Synchronization

File: orchestrator/state_sync.py

Purpose:

Ensure all components (API, workers, database) have consistent session
state.

Responsibilities:

-   Sync session state between Redis and PostgreSQL
-   Cache active sessions in Redis
-   Provide fast lookup for session status

Use Redis as a **fast state cache layer**.

Example:

set_session_state(session_id, state)\
get_session_state(session_id)\
sync_state_to_db(session_id)

------------------------------------------------------------------------

# Session Tracker

File: orchestrator/session_tracker.py

Purpose:

Track active sessions and monitor progress.

Responsibilities:

-   Track running sessions
-   Detect stuck or inactive sessions
-   Provide session statistics

Example:

get_active_sessions()\
get_completed_sessions()\
get_failed_sessions()

------------------------------------------------------------------------

# Integration with FastAPI

Update API endpoints to use session manager.

## Start Interview

POST /start-interview

Flow:

1.  Create session in database
2.  Set status = CREATED
3.  Push task to Redis queue
4.  Update status = QUEUED
5.  Return session_id

------------------------------------------------------------------------

## Get Session Status

GET /session-status/{session_id}

Return:

{ "session_id": "123", "status": "PROCESSING", "risk_score": 0.65,
"last_updated": "timestamp" }

------------------------------------------------------------------------

# Worker Integration

Update worker tasks to maintain session state.

Example flow inside tasks.py:

1.  update status → PROCESSING
2.  update status → VIDEO_PROCESSING
3.  update status → AUDIO_PROCESSING
4.  update status → EVALUATING
5.  update status → COMPLETED

On failure:

update status → FAILED

------------------------------------------------------------------------

# Session Timeout Handling

Implement timeout detection.

If a session is stuck in PROCESSING for too long:

-   mark as FAILED
-   log error
-   optionally retry

Example:

if current_time - start_time \> TIMEOUT_LIMIT:\
mark_session_failed(session_id)

------------------------------------------------------------------------

# Redis Caching Layer

Use Redis to store:

-   active session states
-   fast lookup of status
-   temporary session data

Benefits:

-   reduces database load
-   improves response time
-   supports real-time tracking

------------------------------------------------------------------------

# Consistency Strategy

Use the following approach:

-   Redis = fast cache (temporary state)
-   PostgreSQL = source of truth (persistent state)

Every important update:

1.  update Redis
2.  update PostgreSQL

------------------------------------------------------------------------

# Expected Output

After completing this module:

-   All sessions have a defined lifecycle
-   Session state is synchronized across system
-   API can fetch real-time session status
-   Workers update session states correctly
-   System can recover from failures
-   Redis improves performance

------------------------------------------------------------------------

# Next Module

Module 5 --- Orchestration Layer & Load Balancing

This module will implement:

-   intelligent task distribution
-   load balancing strategies
-   worker selection logic
-   distributed scheduling system
