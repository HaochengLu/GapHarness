def parse_int(value, default=0):
    text = str(value).strip()
    if text == '':
        return default
    return int(text)
