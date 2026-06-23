def group_by(rows, key):
    out = {}
    for row in rows:
        out.setdefault(row[key], []).append(row)
    return out
