def overlaps(left, right):
    return max(left[0], right[0]) <= min(left[1], right[1])
