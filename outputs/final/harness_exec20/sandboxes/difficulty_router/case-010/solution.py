def moving_average(values, window):
    return [sum(values[:window]) / window]
