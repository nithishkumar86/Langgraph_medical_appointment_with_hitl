from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
load_dotenv()
from config import Settings
from sqlalchemy import create_engine,text
from functools import lru_cache
from sqlalchemy import create_engine




# singleton model loading

@lru_cache(maxsize=1)
def get_model():
    return ChatGroq(
        model=Settings().LLM,
        api_key=Settings().GROQ_API_KEY
    )


@lru_cache(maxsize=1)
def get_engine():
    engine = create_engine(
        f"postgresql+psycopg2://postgres:nithish@localhost:5432/{Settings().DATABASE_NAME}"
    )
    return engine


# Python will:
# Run the function once.
# Store the result.
# Next time you call it → return stored result.
# Do NOT run the function again.

# If:
# @lru_cache(maxsize=1)

# It will only remember one result.
# Since get_engine() has no parameters,
# there is only one possible result anyway.
# So:
# First call → creates engine
# Future calls → reuse same engine
# Boom. Singleton.