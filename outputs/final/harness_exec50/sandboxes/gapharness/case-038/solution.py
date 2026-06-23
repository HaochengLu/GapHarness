def parse_duration(value):
    amount = int(value[:-1])
    unit = value[-1]
    if unit == 'h':
        return amount * 3600
    if unit == 'm':
        return amount * 60
    return amount
