class Handler:
    def __init__(self, name, format):
        self.name = name
        self.format = format
        self.noepyCheckType = None
        self.noepyLoadModel = None

    def __repr__(self):
        return self.name
