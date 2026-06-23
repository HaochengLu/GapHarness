import json


def parse_json_lines(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]
