def parse_key_values(text):
    return dict(line.split('=') for line in text.splitlines())
