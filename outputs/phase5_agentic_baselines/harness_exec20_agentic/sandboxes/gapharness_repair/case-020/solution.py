def dedupe_by_id(records):
    seen = set()
    out = []
    for row in records:
        if row['id'] not in seen:
            seen.add(row['id'])
            out.append(row)
    return out
