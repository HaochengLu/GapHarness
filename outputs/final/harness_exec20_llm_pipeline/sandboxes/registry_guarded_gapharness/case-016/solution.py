def sort_records(records):
    return sorted(records, key=lambda row: (row['score'], row['name']))
