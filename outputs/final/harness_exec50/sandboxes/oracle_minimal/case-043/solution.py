def average(values, default=0):
    if not values:
        return default
    return sum(values) / len(values)
