def copyemptydict(a):
    b = dict()
    for item in a.keys():
        b[item] = []
    return b
