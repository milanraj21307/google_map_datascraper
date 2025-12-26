import re

def is_valid_email(email):
    if not email:
        return False
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def is_valid_phone(phone):
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 8

def validate(company):
    issues = []

    if not company.website:
        issues.append("Missing website")

    if not is_valid_email(company.email):
        issues.append("Invalid email")

    if not is_valid_phone(company.phone):
        issues.append("Invalid phone")

    company.validation_status = "OK" if not issues else "; ".join(issues)
