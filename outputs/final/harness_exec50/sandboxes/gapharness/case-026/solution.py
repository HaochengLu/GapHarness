def env_flag(value):
    return str(value).strip().lower() not in {'', '0', 'false', 'no', 'off'}
