def parse_tags(value):
    return [tag.strip().lower() for tag in value.split(',') if tag.strip()]
