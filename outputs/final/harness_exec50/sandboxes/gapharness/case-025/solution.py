def parse_iso_date(value):
    year, month, day = value.split('-')
    return {'year': int(year), 'month': int(month), 'day': int(day)}
