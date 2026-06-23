def stem(path):
    name = path.rstrip('/').split('/')[-1]
    return name.rsplit('.', 1)[0]
