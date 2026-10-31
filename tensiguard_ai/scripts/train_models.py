"""Create versioned metadata for the explainable rule fallback."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ai import app

def main() -> None:
    from ai import SessionLocal, train_models
    db = SessionLocal()
    try:
        print(train_models(db))
    finally:
        db.close()
if __name__ == "__main__": main()
