def reserve(stock, sku, qty):
    out = dict(stock)
    out[sku] = out.get(sku, 0) - qty
    return out
