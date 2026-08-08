"""Configuration — all env vars and constants live here."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "google/gemini-2.5-flash")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

# --- Interview parameters ---
MIN_QUESTIONS: int = 8
MAX_QUESTIONS: int = 12
NUM_INTERVIEW_DAYS: int = 4
MIN_MODULES_COVERED: int = 3
FOLLOW_UP_BUDGET: int = 4

# --- Core AI topic days (used for priority scoring) ---
CORE_AI_DAYS: set[int] = set(range(7, 16)) | set(range(21, 25))  # Days 7-15, 21-24
