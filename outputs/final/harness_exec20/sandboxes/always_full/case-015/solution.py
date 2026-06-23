def apply_defaults(config, defaults):
    out = dict(defaults)
    out.update(config)
    return out
