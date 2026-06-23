def group_by(rows, key):
    out = {}
    for row in rows:
        out[row[key]] = row
    return out
