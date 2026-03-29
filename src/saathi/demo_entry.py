"""Entry point for the saathi-demo command. Launches the Streamlit app."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    demo_app = Path(__file__).parent.parent.parent / "demo" / "app.py"
    sys.exit(
        subprocess.call([sys.executable, "-m", "streamlit", "run", str(demo_app)])
    )


if __name__ == "__main__":
    main()
