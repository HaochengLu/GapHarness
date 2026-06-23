def redact_token(value):
    return value[:4] + '...' + value[-4:]
