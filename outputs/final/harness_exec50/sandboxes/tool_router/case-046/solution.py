def page(items, page_number, size):
    start = page_number * size
    return items[start:start + size]
