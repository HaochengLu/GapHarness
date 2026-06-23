def normalize_path(value):
    parts = [part for part in value.split('/') if part]
    return '/' + '/'.join(parts)
