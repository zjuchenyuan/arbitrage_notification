def instance(*args, **kwargs):
    def instantiate(cls):
        return cls(*args, **kwargs)
    return instantiate
