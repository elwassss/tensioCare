"""TensiGuard DZ AI service: educational blood-pressure decision support."""
import json, logging, os, uuid
from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship as orm_relationship, sessionmaker
from sqlalchemy.pool import StaticPool

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
LOGGER = logging.getLogger("tensiguard")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tensiguard.db")
MODEL_VERSION = os.getenv("MODEL_VERSION", "rules-v1.0")
ESCALATION_MINUTES = int(os.getenv("ESCALATION_MINUTES", "15"))
DISCLAIMER = "Educational decision support only; not a diagnosis. Contact a healthcare professional for high readings or concerning symptoms."
if DATABASE_URL.startswith("sqlite") and ":memory:" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(20), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    language: Mapped[str] = mapped_column(String(5), default="fr")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    contacts = orm_relationship("EmergencyContact", back_populates="patient", cascade="all, delete-orphan")
    readings = orm_relationship("BloodPressureReading", back_populates="patient", cascade="all, delete-orphan")

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    patient = orm_relationship("Patient", back_populates="contacts")

class BloodPressureReading(Base):
    __tablename__ = "blood_pressure_readings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    systolic: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    pulse: Mapped[int] = mapped_column(Integer, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    source: Mapped[str] = mapped_column(String(20), default="manual")
    symptoms: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    patient = orm_relationship("Patient", back_populates="readings")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    reading_id: Mapped[str] = mapped_column(ForeignKey("blood_pressure_readings.id"), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    reasons: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    risk_assessment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("risk_assessments.id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class Medication(Base):
    __tablename__ = "medications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    dosage: Mapped[str] = mapped_column(String(120), nullable=False)
    schedule: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MeasurementReminder(Base):
    __tablename__ = "measurement_reminders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(engine)
def utcnow() -> datetime: return datetime.now(timezone.utc)
def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None: return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
def get_db() -> Session:
    db = SessionLocal()
    try: yield db
    finally: db.close()

class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120); age: int = Field(ge=18, le=120)
    sex: str = Field(pattern=r"^(male|female|other)$"); weight_kg: float = Field(gt=20, le=300)
    height_cm: float = Field(gt=80, le=250); phone_number: str = Field(min_length=7, max_length=30)
    language: str = Field(default="fr", pattern=r"^(ar|fr|en)$")
class PatientOut(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str; created_at: datetime
class ContactCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120); relationship: str = Field(max_length=50)
    phone_number: str = Field(min_length=7, max_length=30); priority: int = Field(ge=1, le=10); is_active: bool = True
class ContactOut(ContactCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
class ReadingCreate(BaseModel):
    systolic: int = Field(ge=40, le=260); diastolic: int = Field(ge=20, le=160); pulse: int = Field(ge=25, le=220)
    measured_at: Optional[datetime] = None; source: str = Field(default="manual", pattern=r"^(manual|bluetooth)$")
    symptoms: List[str] = Field(default_factory=list); notes: str = Field(default="", max_length=1000)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90); longitude: Optional[float] = Field(default=None, ge=-180, le=180)
class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; systolic: int; diastolic: int; pulse: int; measured_at: datetime; source: str; symptoms: List[str]; notes: str
class EscalationRequest(BaseModel):
    reading_id: str; acknowledged: bool = False; latitude: Optional[float] = None; longitude: Optional[float] = None
class MissedCheck(BaseModel): missed_days: int = Field(default=0, ge=0, le=30)

EMERGENCY_SYMPTOMS = {"chest pain", "severe headache", "shortness of breath", "fainting", "vision problems", "weakness on one side"}

def classify_bp(systolic: int, diastolic: int, symptoms: Optional[List[str]] = None) -> str:
    """Educational AHA-style category mapping, not a diagnosis."""
    symptoms = {x.lower() for x in symptoms or []}
    # Emergency symptoms override numerical categories for safe escalation.
    if symptoms & EMERGENCY_SYMPTOMS: return "Hypertensive Crisis / Urgent"
    if systolic > 180 or diastolic > 120: return "Hypertensive Crisis / Urgent"
    if systolic >= 140 or diastolic >= 90: return "Hypertension Stage 2"
    if systolic >= 130 or diastolic >= 80: return "Hypertension Stage 1"
    if systolic >= 120: return "Elevated"
    return "Normal"

def line_slope(values: List[float]) -> float:
    if len(values) < 2: return 0.0
    x = list(range(len(values))); xm = mean(x); ym = mean(values)
    den = sum((v-xm)**2 for v in x)
    return sum((a-xm)*(b-ym) for a,b in zip(x,values))/den if den else 0.0

class AdvisoryService:
    def history(self, db: Session, patient_id: str, days: int = 30) -> List[BloodPressureReading]:
        cutoff = utcnow() - timedelta(days=days)
        return db.query(BloodPressureReading).filter(BloodPressureReading.patient_id == patient_id,
            BloodPressureReading.measured_at >= cutoff).order_by(BloodPressureReading.measured_at).all()
    def all_history(self, db: Session, patient_id: str) -> List[BloodPressureReading]:
        return db.query(BloodPressureReading).filter(BloodPressureReading.patient_id == patient_id).order_by(BloodPressureReading.measured_at).all()
    def trend(self, db: Session, patient_id: str) -> Dict[str, Any]:
        rows = self.history(db, patient_id, 30); periods: Dict[str, Any] = {}
        for days in (7,14,30):
            part = [r for r in rows if to_utc(r.measured_at) >= utcnow()-timedelta(days=days)]
            ss = [r.systolic for r in part]; dd = [r.diastolic for r in part]
            periods[str(days)] = {"reading_count": len(part), "systolic_average": round(mean(ss),1) if ss else None,
                "diastolic_average": round(mean(dd),1) if dd else None, "systolic_slope": round(line_slope(ss),2),
                "diastolic_slope": round(line_slope(dd),2), "systolic_variability": round(pstdev(ss),1) if len(ss)>1 else 0,
                "diastolic_variability": round(pstdev(dd),1) if len(dd)>1 else 0}
        signals: List[str] = []
        ss7 = [r.systolic for r in rows if to_utc(r.measured_at) >= utcnow()-timedelta(days=7)]
        ss14 = [r.systolic for r in rows if to_utc(r.measured_at) >= utcnow()-timedelta(days=14)]
        if line_slope(ss7)>1.5: signals.append("Systolic pressure is rising this week")
        if line_slope(ss14)>1.5: signals.append("Systolic pressure is deteriorating this month")
        elif line_slope(ss14)<-1.5: signals.append("Systolic pressure is improving this month")
        morning = [r.systolic for r in rows if r.measured_at.hour < 12]
        evening = [r.systolic for r in rows if 17 <= r.measured_at.hour < 23]
        if morning and mean(morning)>=130: signals.append("Morning readings are high")
        if evening and mean(evening)>=130: signals.append("Evening readings are high")
        if ss14 and pstdev(ss14)>15: signals.append("Blood pressure has high variability")
        return {"periods": periods, "signals": signals,
            "morning_systolic_average": round(mean(morning),1) if morning else None,
            "evening_systolic_average": round(mean(evening),1) if evening else None, "disclaimer": DISCLAIMER}
    def anomalies(self, rows: List[BloodPressureReading]) -> Dict[str, Any]:
        findings=[]
        for i,r in enumerate(rows):
            if r.systolic <= r.diastolic: findings.append({"reading_id":r.id,"kind":"suspicious_values","message":"Systolic pressure is not above diastolic pressure."})
            if r.systolic<70 or r.systolic>260 or r.diastolic<40 or r.diastolic>160 or r.pulse<25 or r.pulse>220:
                findings.append({"reading_id":r.id,"kind":"extreme_value","message":"This reading contains an extreme value and should be checked again."})
            if i and abs(r.systolic-rows[i-1].systolic)>=30: findings.append({"reading_id":r.id,"kind":"sudden_spike","message":"The systolic pressure changed suddenly between measurements."})
        return {"count":len(findings),"findings":findings,"disclaimer":DISCLAIMER}
    def risk(self, db: Session, patient_id: str) -> Dict[str, Any]:
        patient=db.get(Patient,patient_id)
        if not patient: raise HTTPException(404,"Patient not found")
        rows=self.history(db,patient_id,7)
        if not rows: return {"risk_level":"Low","risk_score":0,"classification":"Insufficient data","reasons":["No readings were found in the last week."],"recommendations":["Take a calm measurement."],"disclaimer":DISCLAIMER}
        latest=rows[-1]; symptoms=[x.strip().lower() for x in latest.symptoms.split(",") if x.strip()]
        score=0; reasons=[]; systolic=latest.systolic; diastolic=latest.diastolic
        if systolic>=180 or diastolic>=120:
            score+=45; reasons.append(f"Systolic pressure is {systolic} mmHg, above the urgent threshold.")
        elif systolic>=140 or diastolic>=90:
            score+=25; reasons.append(f"Latest pressure is {systolic}/{diastolic}, which is very high.")
        elif systolic>=130 or diastolic>=80: score+=12
        if latest.pulse>=120: score+=12; reasons.append("The pulse is very high.")
        elif latest.pulse<45: score+=6
        high=[r for r in rows if r.systolic>=130 or r.diastolic>=80]
        if len(high)>=3: score+=min(20,len(high)*4); reasons.append(f"{len(high)} high readings were recorded in the last seven days.")
        if line_slope([r.systolic for r in rows])>1.5: score+=10; reasons.append("Systolic pressure is rising over the last week.")
        ss=[r.systolic for r in rows]; variability=pstdev(ss) if len(ss)>1 else 0
        if variability>15: score+=8; reasons.append("Blood pressure readings vary more than usual.")
        urgent=set(symptoms)&EMERGENCY_SYMPTOMS
        if urgent: score+=35; reasons.append("Urgent symptoms were reported, including "+", ".join(sorted(urgent))+".")
        if set(symptoms)-EMERGENCY_SYMPTOMS: score+=7; reasons.append("A symptom was reported with the latest measurement.")
        if patient.age>=65: score+=5
        score=min(score,100)
        if urgent or score>=75 or systolic>=180 or diastolic>=120: level="Urgent"
        elif score>=50: level="High"
        elif score>=25: level="Watch"
        else: level="Low"
        recommendations=["Sit down and rest quietly.","Repeat the measurement after five minutes if it is safe.","Contact a healthcare professional if it stays high."]
        if level=="Urgent": recommendations=["Call emergency assistance now.","Do not drive yourself.","Tell your family and stay with someone you trust."]
        assessment=RiskAssessment(patient_id=patient.id,reading_id=latest.id,risk_level=level,risk_score=score,
            reasons=json.dumps(reasons),recommendations=json.dumps(recommendations),model_version=MODEL_VERSION)
        db.add(assessment); db.commit(); db.refresh(assessment)
        return {"risk_level":level,"risk_score":score,"classification":classify_bp(systolic,diastolic,symptoms),
            "reasons":reasons,"recommendations":recommendations,"model_version":MODEL_VERSION,
            "assessed_reading_id":latest.id,"assessment_id":assessment.id,"disclaimer":DISCLAIMER}
    def adherence(self,db:Session,patient_id:str,missed_days:int=0)->Dict[str,Any]:
        rows=self.all_history(db,patient_id)
        misses=db.query(MeasurementReminder).filter(MeasurementReminder.patient_id==patient_id,MeasurementReminder.status=="missed").count()
        times=[r.measured_at.replace(tzinfo=None) if r.measured_at.tzinfo else r.measured_at for r in rows]
        intervals=[(times[i]-times[i-1]).total_seconds()/86400 for i in range(1,len(times))]
        irregularity=pstdev(intervals) if len(intervals)>1 else 0
        frequency=len(rows)/max(1,(utcnow().replace(tzinfo=None)-times[0]).days) if times else 0
        probability=min(.95,.15+irregularity*.025+misses*.08+missed_days*.08+max(0,.25-frequency*.03))
        adherence=round(max(0,min(100,100-probability*100)))
        hour=int(round(mean([t.hour for t in times]))) if times else 8
        return {"adherence_score":adherence,"probability_of_missing_next_measurement":round(probability,2),
            "recommended_reminder_time":f"{hour:02d}:00",
            "explanation":f"Based on {len(rows)} measurements, {misses} missed reminders, and measurement regularity."}
    def reminder_times(self,rows:List[BloodPressureReading])->Dict[str,str]:
        morning=[r.measured_at.hour for r in rows if r.measured_at.hour<12]
        evening=[r.measured_at.hour for r in rows if r.measured_at.hour>=17]
        return {"morning":f"{(int(round(mean(morning))) if morning else 8):02d}:00","evening":f"{(int(round(mean(evening))) if evening else 20):02d}:00"}
advisory=AdvisoryService()

MESSAGES={
"urgent":{"en":"Your blood pressure is dangerously high. Sit down, stay calm, call emergency assistance, and tell your family.","fr":"Votre tension est dangereusement élevée. Asseyez-vous, restez calme, appelez les secours et prévenez votre famille.","ar":"ضغط الدم مرتفع بصورة خطيرة. اجلس، وابقَ هادئاً، واتصل بخدمات الطوارئ وأخبر عائلتك."},
"high":{"en":"Your blood pressure is high. Please sit down, stay calm, and contact your doctor or family member.","fr":"Votre tension est élevée. Asseyez-vous, restez calme et contactez votre médecin ou un proche.","ar":"ضغط الدم مرتفع. اجلس، وابقَ هادئاً، واتصل بطبيبك أو بأحد أفراد عائلتك."},
"watch":{"en":"Please measure again after five minutes and rest quietly.","fr":"Mesurez à nouveau après cinq minutes et reposez-vous tranquillement.","ar":"قِس ضغطك مرة أخرى بعد خمس دقائق وارقد بهدوء."},
"low":{"en":"Your reading is normal today. Continue your usual care plan.","fr":"Votre mesure est normale aujourd’hui. Continuez votre suivi habituel.","ar":"قراءة ضغطك طبيعية اليوم. تابع خطة الرعاية المعتادة."}}
def localized_message(language:str,key:str)->str: return MESSAGES[key].get(language,MESSAGES[key]["en"])

app=FastAPI(title="TensiGuard DZ AI",version="1.0.0",description=DISCLAIMER)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","*").split(','),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.exception_handler(Exception)
async def unhandled(request:Any,exc:Exception):
    LOGGER.exception("Unhandled request error: %s",exc)
    return JSONResponse(status_code=500,content={"detail":"Internal service error","disclaimer":DISCLAIMER})
@app.get("/health")
def health(): return {"status":"ok","service":"tensiguard-ai","model_version":MODEL_VERSION,"disclaimer":DISCLAIMER}
@app.post("/patients",response_model=PatientOut,status_code=201)
def create_patient(payload:PatientCreate,db:Session=Depends(get_db)):
    patient=Patient(**payload.model_dump()); db.add(patient); db.commit(); db.refresh(patient); return patient
@app.get("/patients/{patient_id}",response_model=PatientOut)
def get_patient(patient_id:str,db:Session=Depends(get_db)):
    patient=db.get(Patient,patient_id)
    if not patient: raise HTTPException(404,"Patient not found")
    return patient
@app.post("/patients/{patient_id}/emergency-contacts",response_model=ContactOut,status_code=201)
def add_contact(patient_id:str,payload:ContactCreate,db:Session=Depends(get_db)):
    if not db.get(Patient,patient_id): raise HTTPException(404,"Patient not found")
    contact=EmergencyContact(patient_id=patient_id,**payload.model_dump()); db.add(contact); db.commit(); db.refresh(contact); return contact
@app.post("/patients/{patient_id}/readings",response_model=ReadingOut,status_code=201)
def add_reading(patient_id:str,payload:ReadingCreate,db:Session=Depends(get_db)):
    if not db.get(Patient,patient_id): raise HTTPException(404,"Patient not found")
    row=BloodPressureReading(patient_id=patient_id,systolic=payload.systolic,diastolic=payload.diastolic,pulse=payload.pulse,
        measured_at=payload.measured_at or utcnow(),source=payload.source,symptoms=", ".join(payload.symptoms),notes=payload.notes)
    db.add(row); db.commit(); db.refresh(row)
    return {"id":row.id,"systolic":row.systolic,"diastolic":row.diastolic,"pulse":row.pulse,"measured_at":row.measured_at,
        "source":row.source,"symptoms":payload.symptoms,"notes":row.notes}
@app.get("/patients/{patient_id}/readings",response_model=List[ReadingOut])
def list_readings(patient_id:str,limit:int=Query(default=100,ge=1,le=1000),db:Session=Depends(get_db)):
    if not db.get(Patient,patient_id): raise HTTPException(404,"Patient not found")
    rows=db.query(BloodPressureReading).filter(BloodPressureReading.patient_id==patient_id).order_by(BloodPressureReading.measured_at.desc()).limit(limit).all()
    output=[]
    for r in reversed(rows): output.append({"id":r.id,"systolic":r.systolic,"diastolic":r.diastolic,"pulse":r.pulse,"measured_at":r.measured_at,"source":r.source,"symptoms":[x.strip() for x in r.symptoms.split(",") if x.strip()],"notes":r.notes})
    return output
@app.get("/patients/{patient_id}/trends")
def trends(patient_id:str,db:Session=Depends(get_db)):
    if not db.get(Patient,patient_id): raise HTTPException(404,"Patient not found")
    return advisory.trend(db,patient_id)
@app.get("/patients/{patient_id}/risk-assessment")
def risk_assessment(patient_id:str,db:Session=Depends(get_db)): return advisory.risk(db,patient_id)
@app.post("/patients/{patient_id}/missed-measurement-check")
def missed_check(patient_id:str,payload:MissedCheck,db:Session=Depends(get_db)):
    if not db.get(Patient,patient_id): raise HTTPException(404,"Patient not found")
    result=advisory.adherence(db,patient_id,payload.missed_days); result["disclaimer"]=DISCLAIMER; return result
@app.post("/patients/{patient_id}/alerts/escalate")
def escalate(patient_id:str,payload:EscalationRequest,db:Session=Depends(get_db)):
    patient=db.get(Patient,patient_id); reading=db.get(BloodPressureReading,payload.reading_id)
    if not patient or not reading or reading.patient_id!=patient_id: raise HTTPException(404,"Patient or reading not found")
    risk=advisory.risk(db,patient_id); contacts=db.query(EmergencyContact).filter(EmergencyContact.patient_id==patient_id,EmergencyContact.is_active==True).order_by(EmergencyContact.priority).all()
    sent=None if payload.acknowledged else (contacts[0] if contacts else None)
    second=contacts[1] if not payload.acknowledged and len(contacts)>1 else None
    symptoms=reading.symptoms or "none reported"; location=None
    if payload.latitude is not None and payload.longitude is not None: location=f"https://maps.google.com/?q={payload.latitude},{payload.longitude}"
    sms_message=None
    if risk["risk_level"]=="Urgent" and sent:
        sms_message=f"TensiGuard DZ: {patient.full_name} - {reading.systolic}/{reading.diastolic} mmHg, pulse {reading.pulse}, symptoms: {symptoms}. Please respond."
        if location: sms_message += " Location: "+location
    alert=Alert(patient_id=patient_id,risk_assessment_id=risk["assessment_id"],alert_type="emergency_sms" if risk["risk_level"]=="Urgent" else "family_notification",message=sms_message or "No urgent alert required.",status="acknowledged" if payload.acknowledged else "sent",acknowledged_at=utcnow() if payload.acknowledged else None)
    db.add(alert); db.commit(); db.refresh(alert)
    return {"alert_id":alert.id,"risk_level":risk["risk_level"],"contact_1_notified":sent.full_name if sent else None,
        "escalate_after_minutes":ESCALATION_MINUTES,"escalate_to_contact_2":second.full_name if second else None,
        "sms_payload":{"recipient":sent.phone_number if sent else None,"message":sms_message},
        "hospital_alert_request":{"hospitalAlertRequest":risk["risk_level"]=="Urgent","patient_name":patient.full_name,
        "reading":f"{reading.systolic}/{reading.diastolic} mmHg","pulse":reading.pulse,"symptoms":symptoms,"location":location,
        "measured_at":reading.measured_at.isoformat(),"summary":"Urgent review requested; this is not a diagnosis."},"disclaimer":DISCLAIMER}
@app.get("/patients/{patient_id}/doctor-report")
def doctor_report(patient_id:str,db:Session=Depends(get_db)):
    patient=db.get(Patient,patient_id)
    if not patient: raise HTTPException(404,"Patient not found")
    rows=advisory.all_history(db,patient_id); latest=rows[-1] if rows else None
    return {"patient":{"id":patient.id,"full_name":patient.full_name,"age":patient.age},"period":"30 days","trend":advisory.trend(db,patient_id),
        "anomalies":advisory.anomalies(rows[-30:]),"latest_reading":{"systolic":latest.systolic,"diastolic":latest.diastolic,"pulse":latest.pulse,"measured_at":latest.measured_at.isoformat()} if latest else None,
        "reminder_plan":advisory.reminder_times(rows[-60:]),"disclaimer":DISCLAIMER}
@app.post("/ai/train-or-update-models")
def train_models(db:Session=Depends(get_db)):
    metadata={"model_version":MODEL_VERSION,"trained_at":utcnow().isoformat(),
      "features":["systolic","diastolic","pulse","recent_high_count","trend","variability","symptoms","age","missed_measurements"],
      "training_rows":db.query(BloodPressureReading).count(),"patient_count":db.query(Patient).count(),"engine":"transparent-rule-fallback"}
    os.makedirs("models",exist_ok=True)
    with open(os.path.join("models","metadata.json"),"w",encoding="utf-8") as f: json.dump(metadata,f,ensure_ascii=False,indent=2)
    return metadata
if __name__=="__main__":
    import uvicorn
    uvicorn.run("ai:app",host=os.getenv("HOST","0.0.0.0"),port=int(os.getenv("PORT","8000")),reload=os.getenv("RELOAD","false").lower()=="true")