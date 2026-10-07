ALLOWED_FRAUD_TYPES = {
    "VOICE_PHISHING",
    "USED_TRADE",
    "INVESTMENT",
    "IDENTITY_THEFT",
}

def base_risk_level(fraud_type: str, amount: int) -> str:
    if fraud_type not in ALLOWED_FRAUD_TYPES:
        raise ValueError("유효하지 않은 사기 유형")

    if fraud_type in {"INVESTMENT", "IDENTITY_THEFT"}:
        return "HIGH"

    if fraud_type in {"VOICE_PHISHING", "USED_TRADE"}:
        return "HIGH" if amount >= 1_000_000 else "MEDIUM"

    return "MEDIUM"

def final_risk_level(fraud_type: str, amount: int, same_account_previous_count: int) -> str:
    # 동일 의심 계좌 신고가 기존 2건 이상이면 현재 신고가 3번째 이상이므로 CRITICAL
    if same_account_previous_count >= 2:
        return "CRITICAL"
    return base_risk_level(fraud_type, amount)
