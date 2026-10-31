"""Seed five realistic demo patients and 60 days of readings."""
import random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ai import Patient, EmergencyContact, BloodPressureReading, SessionLocal

SCENARIOS = ["stable", "worsening", "irregular", "missed", "urgent"]
NAMES = ["Ahmed Benali", "Fatima Boudiaf", "Karim Saidi", "Nadia Mansouri", "Rachid Hamidi"]

def run() -> None:
    db = SessionLocal()
    db.query(BloodPressureReading).delete(); db.query(EmergencyContact).delete(); db.query(Patient).delete(); db.commit()
    random.seed(42)
    now = datetime.now(timezone.utc)
    for index, (name, scenario) in enumerate(zip(NAMES, SCENARIOS)):
        patient = Patient(full_name=name, age=58 + index * 3, sex="female" if index % 2 else "male",
                          weight_kg=70.0 + index, height_cm=168.0 + index, phone_number=f"+213555010{index}", language="ar" if index == 0 else "fr")
        db.add(patient); db.flush()
        db.add(EmergencyContact(patient_id=patient.id, full_name=f"Family {index+1}", relationship="family", phone_number=f"+213666010{index}", priority=1, is_active=True))
        for days_ago in range(60, -1, -1):
            if scenario == "irregular" and random.random() < .22: continue
            if scenario == "missed" and days_ago % 9 == 0: continue
            base = 118 + (60-days_ago) * (0.8 if scenario == "worsening" else 0)
            if scenario == "urgent" and days_ago < 4: base = 175
            systolic = round(base + random.gauss(0, 7)); diastolic = round(76 + random.gauss(0, 5))
            for hour in (8, 20) if scenario != "irregular" or random.random()>.35 else (12,):
                measured = now - timedelta(days=days_ago, hours=now.hour-hour, minutes=random.randint(0,25))
                db.add(BloodPressureReading(patient_id=patient.id, systolic=min(systolic,195), diastolic=min(diastolic,115),
                    pulse=random.randint(62,82), measured_at=measured, source="manual",
                    symptoms="chest pain" if scenario == "urgent" and days_ago < 4 else ""))
    db.commit(); db.close(); print("Seeded 5 patients with realistic 60-day readings.")
if __name__ == "__main__": run()
