def normalize_phone(value):
    return ''.join(ch for ch in value if ch.isdigit())
