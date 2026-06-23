def is_palindrome(value):
    cleaned = ''.join(ch.lower() for ch in value if ch.isalnum())
    return cleaned == cleaned[::-1]
