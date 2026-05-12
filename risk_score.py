# risk_score.py

def calculate_risk(is_known, confidence, time_hour,
                   visit_count=1,
                   wrong_room=False,
                   wrong_otp=False):

    risk = 0

    # Unknown person → high risk
    if not is_known:
        risk += 10
    else:
        risk += 0

    # Night time risk
    if time_hour < 6 or time_hour > 22:
        risk += 20

    # Wrong room number
    if wrong_room:
        risk += 25

    # Wrong OTP (very serious)
    if wrong_otp:
        risk += 40

    # clamp 0–100
    risk = max(0, min(100, int(risk)))

    return risk


def get_decision(risk):
    """
    Convert risk score into action
    """
    if risk <= 30:
        return "OPEN"
    elif risk <= 70:
        return "WARNING"
    else:
        return "DENY"