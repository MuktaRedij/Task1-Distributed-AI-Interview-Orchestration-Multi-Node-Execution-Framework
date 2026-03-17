"""
Configuration file for AI Interview Orchestrator
Stores environment configuration and loads from .env files if available
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'ai_interview_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

# Worker Configuration
WORKER_CONCURRENCY = int(os.getenv('WORKER_CONCURRENCY', '4'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

# Database URL for SQLAlchemy
DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}'
