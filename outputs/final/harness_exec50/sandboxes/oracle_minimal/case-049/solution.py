def ensure_prefix(value, prefix):
    if value.startswith(prefix):
        return value
    return prefix + value
