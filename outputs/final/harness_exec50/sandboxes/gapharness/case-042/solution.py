def window_sum(values, window):
    return [sum(values[i:i + window]) for i in range(len(values) - window + 1)]
