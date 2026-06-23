def reserve(stock, sku, qty):
    out = dict(stock)
    out[sku] -= 1
    return out
