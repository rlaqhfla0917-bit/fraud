import json
import os
import uuid
from datetime import datetime, timezone

from .risk import ALLOWED_FRAUD_TYPES, final_risk_level
from .store import build_store
from .validation import ALLOWED_STATUS, validate_create, validate_status

STORE = build_store()

def response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }

def parse_body(event):
    body = event.get("body")
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    return json.loads(body)

def route(event):
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("path") or event.get("rawPath") or "/"
    path_params = event.get("pathParameters") or {}
    return method, path, path_params

def create_report(event):
    try:
        payload = parse_body(event)
        validate_create(payload)
        fraud_type = payload["fraud_type"]
        if fraud_type not in ALLOWED_FRAUD_TYPES:
            return response(400, {"error": "유효하지 않은 사기 유형"})

        suspect_account = payload.get("suspect_account")
        prior_count = STORE.count_by_account(suspect_account) if suspect_account else 0
        risk = final_risk_level(fraud_type, int(payload["amount"]), prior_count)

        suspicion_id = "FRD-" + uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "suspicion_id": suspicion_id,
            "fraud_type": fraud_type,
            "victim_name": payload["victim_name"],
            "victim_phone": payload["victim_phone"],
            "amount": int(payload["amount"]),
            "status": "RECEIVED",
            "risk_level": risk,
            "created_at": now,
            "updated_at": now,
        }
        if suspect_account:
            item["suspect_account"] = suspect_account
        if payload.get("description"):
            item["description"] = payload["description"]

        STORE.put_report(item)

        return response(201, {
            "suspicion_id": suspicion_id,
            "status": "RECEIVED",
            "risk_level": risk,
            "message": "신고가 접수되었습니다. 담당자가 검토 후 연락드립니다.",
        })
    except ValueError as e:
        return response(400, {"error": str(e)})
    except json.JSONDecodeError:
        return response(400, {"error": "요청 본문이 올바른 JSON이 아닙니다"})

def list_reports(event):
    # scan()을 사용하지 않고 GSI2(status + created_at)를 상태별 query
    statuses = list(ALLOWED_STATUS)
    items = STORE.list_by_statuses(statuses)
    return response(200, {"items": items, "count": len(items)})

def get_report(event, suspicion_id: str):
    item = STORE.get_report(suspicion_id)
    if not item:
        return response(404, {"error": "신고를 찾을 수 없습니다"})
    return response(200, item)

def update_status(event, suspicion_id: str):
    try:
        payload = parse_body(event)
        status = payload.get("status")
        validate_status(status)
        if not STORE.get_report(suspicion_id):
            return response(404, {"error": "신고를 찾을 수 없습니다"})
        updated = STORE.update_status(suspicion_id, status)
        return response(200, updated)
    except ValueError as e:
        return response(400, {"error": str(e)})
    except json.JSONDecodeError:
        return response(400, {"error": "요청 본문이 올바른 JSON이 아닙니다"})

def lambda_handler(event, context):
    method, path, params = route(event)
    suspicion_id = params.get("id") or params.get("suspicion_id")

    if method == "POST" and path.endswith("/fraud-reports"):
        return create_report(event)

    if method == "GET" and path.endswith("/fraud-reports"):
        return list_reports(event)

    if method == "GET" and suspicion_id and "/fraud-reports/" in path:
        return get_report(event, suspicion_id)

    if method == "PUT" and suspicion_id and path.endswith("/status"):
        return update_status(event, suspicion_id)

    return response(404, {"error": "지원하지 않는 경로입니다"})
