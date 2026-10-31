from fastapi.testclient import TestClient
from ai import app
client = TestClient(app)

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_create_and_read_patient():
    payload = {'full_name':'Test Patient','age':68,'sex':'female','weight_kg':72.5,'height_cm':165,'phone_number':'+213555000001','language':'fr'}
    created = client.post('/patients',json=payload)
    assert created.status_code == 201
    patient_id = created.json()['id']
    fetched = client.get(f'/patients/{patient_id}')
    assert fetched.status_code == 200
    assert fetched.json()['full_name'] == 'Test Patient'
