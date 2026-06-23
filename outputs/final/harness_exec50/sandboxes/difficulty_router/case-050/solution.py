import json


def parse_json_lines(text):
    return [json.loads(text)]
