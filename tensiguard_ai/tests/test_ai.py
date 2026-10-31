from ai import classify_bp, EMERGENCY_SYMPTOMS, line_slope

def test_normal_classification():
    assert classify_bp(118,78,[]) == "Normal"

def test_elevated_classification():
    assert classify_bp(125,76,[]) == "Elevated"

def test_stage_two_classification():
    assert classify_bp(145,92,[]) == "Hypertension Stage 2"

def test_crisis_classification():
    assert classify_bp(182,122,[]) == "Hypertensive Crisis / Urgent"

def test_emergency_symptom_overrides_number():
    assert classify_bp(110,70,["chest pain"] ) == "Hypertensive Crisis / Urgent"

def test_rising_trend():
    assert line_slope([110,112,115,120]) > 2

def test_emergency_symptoms_set():
    assert "fainting" in EMERGENCY_SYMPTOMS
