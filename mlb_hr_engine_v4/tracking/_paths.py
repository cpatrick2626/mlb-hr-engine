import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("TRACKING_DATA_DIR", str(Path(__file__).parent)))
