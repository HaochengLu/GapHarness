def zscores(values):
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    stdev = variance ** 0.5
    return [(value - mean) / stdev for value in values]
