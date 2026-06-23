def page(items, page_number, size):
    start = (page_number - 1) * size
    return items[start:start + size]
