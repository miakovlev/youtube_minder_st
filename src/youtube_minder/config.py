from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Main directories
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
TRANSCRIPTIONS_DIR = DATA_DIR / "transcriptions"
