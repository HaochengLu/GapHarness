def parse_key_values(text):
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, value = line.split('=', 1)
        out[key.strip()] = value.strip()
    return out
