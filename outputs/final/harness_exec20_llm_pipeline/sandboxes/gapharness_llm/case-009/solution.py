def flatten_once(values):
    out = []
    for item in values:
        if isinstance(item, list):
            out.extend(item)
        else:
            out.append(item)
    return out
