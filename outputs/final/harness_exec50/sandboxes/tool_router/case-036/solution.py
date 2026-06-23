def word_counts(text):
    out = {}
    for word in text.lower().split():
        out[word] = out.get(word, 0) + 1
    return out
