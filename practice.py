def deep_flatten(iterable):
    if isinstance(iterable, str):
        pass


    elif isinstance(iterable, (list, tuple)):
        res = []
        for i in range(len(iterable)):
            res.append(iterable[i])
        return res


a = [[(1, 2), (3, 4)], [(5, 6), (7, 8)]]
#a = ([[1, [2, 3]], 4, 5])
print(len(a))
