"""Run the site and the API locally on one port.

    python run_local.py              http://localhost:8000
    python run_local.py --lang ru    consultant answers in Russian
    python run_local.py --port 8080
"""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "immoonity-app"))


def main() -> None:
    parser = argparse.ArgumentParser(description="IMMOONITY: site + API")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--lang", choices=("en", "ru"), default="en")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    try:
        from app import create_app
    except ModuleNotFoundError as exc:
        sys.exit(f"Package {exc.name} is not installed: pip install -r requirements.txt")

    app = create_app(site_dir=ROOT / "immoonity-site")
    url = f"http://localhost:{args.port}/"
    page = url + ("?lang=ru" if args.lang == "ru" else "") + "#demo"
    print(f"\n  IMMOONITY: {page}")
    print(f"  API:       {url}api/health\n")
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(page)).start()
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
