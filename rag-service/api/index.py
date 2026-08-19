import sys
from pathlib import Path

# Add project root to sys.path so 'app' package is discoverable in Vercel serverless runtime
_current_dir = Path(__file__).resolve().parent
_project_root = _current_dir.parent

if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.main import app
