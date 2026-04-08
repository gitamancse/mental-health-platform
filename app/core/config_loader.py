from dotenv import load_dotenv
from pathlib import Path
import tzlocal

# Root folder (mental-health-platform/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

if not ENV_PATH.exists():
    raise RuntimeError(f".env file not found at {ENV_PATH}")

load_dotenv(dotenv_path=ENV_PATH, override=True)

# Import after loading env
from app.core.config import settings

# App timezone
app_tz = tzlocal.get_localzone()