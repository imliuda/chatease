class Message(object):
    def __init__(self):
        self.type = None
        self.complete = False
        self.elements = []

    def __str__(self):
        pass

    def __bytes__(self):
        pass


class Element(object):
    pass