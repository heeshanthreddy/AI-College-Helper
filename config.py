from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "in", "on", "at", "of", "to", "for", "with",
    "and", "or", "what", "how", "why", "when",
    "where", "which", "can", "could", "please",
    "explain", "tell", "me", "about"
}