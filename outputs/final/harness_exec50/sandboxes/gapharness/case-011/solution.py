def parse_csv_row(row):
    return [part.strip() for part in row.split(',')]
