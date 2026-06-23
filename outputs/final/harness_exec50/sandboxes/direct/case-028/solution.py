def mask_email(value):
    name, domain = value.split('@', 1)
    return '***@' + domain
