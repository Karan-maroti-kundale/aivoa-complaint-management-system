import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://aivoa:aivoa@localhost:5432/aivoa")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AIVOA_GROQ_MODEL = os.getenv("AIVOA_GROQ_MODEL", "gemma2-9b-it")
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
