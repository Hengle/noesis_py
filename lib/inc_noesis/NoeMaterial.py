class NoeMaterial:
    def __init__(self, name, unk1):
        self.name = name
        self.unk1 = unk1
        self.texture = None

    def setDiffuseColor(self, color):
        self.color = color

    def setTexture(self, texture):
        self.texture = texture

    def __repr__(self):
        return "<NoeMaterial name: {self.name}>".format(**locals())
