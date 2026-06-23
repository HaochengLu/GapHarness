def is_anagram(left, right):
    clean_left = sorted(ch.lower() for ch in left if ch.isalnum())
    clean_right = sorted(ch.lower() for ch in right if ch.isalnum())
    return clean_left == clean_right
