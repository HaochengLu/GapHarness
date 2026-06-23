def parse_bool(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}
