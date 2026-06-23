def expired(created_at, now, ttl):
    return now - created_at >= ttl
