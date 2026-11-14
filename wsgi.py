import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "immoonity-app"))

from app import create_app

app = create_app(site_dir=ROOT / "immoonity-site")
