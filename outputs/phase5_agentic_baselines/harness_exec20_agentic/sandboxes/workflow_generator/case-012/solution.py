def is_valid_email(value):
    return '@' in value and '.' in value.split('@')[-1]
