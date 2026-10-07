from src.risk import base_risk_level, final_risk_level

def test_voice_phishing_threshold():
    assert base_risk_level("VOICE_PHISHING", 999_999) == "MEDIUM"
    assert base_risk_level("VOICE_PHISHING", 1_000_000) == "HIGH"

def test_investment_is_high():
    assert base_risk_level("INVESTMENT", 1) == "HIGH"

def test_same_account_third_report_is_critical():
    assert final_risk_level("USED_TRADE", 100_000, 2) == "CRITICAL"
