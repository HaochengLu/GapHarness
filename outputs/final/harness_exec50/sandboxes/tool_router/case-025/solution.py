def parse_iso_date(value):
    month, day, year = value.split('/')
    return {'year': int(year), 'month': int(month), 'day': int(day)}
