import re

PHONE_RE = re.compile(r"^010-\d{3,4}-\d{4}$")
ALLOWED_STATUS = {"RECEIVED", "REVIEWING", "CONFIRMED", "DISMISSED", "CLOSED"}

def validate_create(payload: dict):
    required = ["fraud_type", "victim_name", "victim_phone", "amount"]
    missing = [key for key in required if payload.get(key) in (None, "")]
    if missing:
        raise ValueError(f"필수 필드 누락: {', '.join(missing)}")

    if len(str(payload["victim_name"])) > 50:
        raise ValueError("victim_name은 최대 50자입니다")

    if not PHONE_RE.match(str(payload["victim_phone"])):
        raise ValueError("victim_phone 형식은 010-xxxx-xxxx 입니다")

    try:
        amount = int(payload["amount"])
    except Exception as e:
        raise ValueError("amount는 정수여야 합니다") from e

    if amount < 0:
        raise ValueError("amount는 0 이상이어야 합니다")

    description = payload.get("description")
    if description and len(str(description)) > 500:
        raise ValueError("description은 최대 500자입니다")

def validate_status(status: str):
    if status not in ALLOWED_STATUS:
        raise ValueError("유효하지 않은 상태값")
