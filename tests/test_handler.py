import importlib
import json
import os

os.environ["LOCAL_MODE"] = "true"
os.environ["TABLE_NAME"] = "fraud-reports"

import src.lambda_function as lf
lf = importlib.reload(lf)

def event(method, path, body=None, path_params=None):
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": path_params or {},
        "body": json.dumps(body) if body is not None else None,
    }

def body(resp):
    return json.loads(resp["body"])

def test_create_get_and_update():
    create = lf.lambda_handler(event("POST", "/fraud-reports", {
        "fraud_type": "VOICE_PHISHING",
        "victim_name": "홍길동",
        "victim_phone": "010-1234-5678",
        "amount": 500000,
        "suspect_account": "110-123-456789",
        "description": "테스트 신고",
    }), None)
    assert create["statusCode"] == 201
    created = body(create)
    assert created["risk_level"] == "MEDIUM"
    sid = created["suspicion_id"]

    get_resp = lf.lambda_handler(event("GET", f"/fraud-reports/{sid}", path_params={"id": sid}), None)
    assert get_resp["statusCode"] == 200

    update = lf.lambda_handler(event("PUT", f"/fraud-reports/{sid}/status", {
        "status": "REVIEWING"
    }, path_params={"id": sid}), None)
    assert update["statusCode"] == 200
    assert body(update)["status"] == "REVIEWING"

def test_third_same_account_is_critical():
    account = "999-999-999999"
    for i in range(3):
        r = lf.lambda_handler(event("POST", "/fraud-reports", {
            "fraud_type": "USED_TRADE",
            "victim_name": f"피해자{i}",
            "victim_phone": "010-1111-2222",
            "amount": 100000,
            "suspect_account": account,
        }), None)
    assert body(r)["risk_level"] == "CRITICAL"

def test_invalid_type_returns_400():
    r = lf.lambda_handler(event("POST", "/fraud-reports", {
        "fraud_type": "UNKNOWN",
        "victim_name": "홍길동",
        "victim_phone": "010-1234-5678",
        "amount": 1000,
    }), None)
    assert r["statusCode"] == 400
