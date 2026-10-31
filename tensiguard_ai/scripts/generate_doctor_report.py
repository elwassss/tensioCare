"""Print a doctor-friendly JSON report for the first demo patient."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ai import Patient, SessionLocal, advisory

def main() -> None:
    db = SessionLocal()
    patient = db.query(Patient).first()
    if not patient:
        print("No patients found. Run scripts/seed_demo_data.py first."); return
    print(json.dumps({"patient":patient.full_name,"trend":advisory.trend(db,patient.id),"risk":advisory.risk(db,patient.id)}, ensure_ascii=False, default=str, indent=2))
if __name__ == "__main__": main()
