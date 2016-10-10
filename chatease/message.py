class Message(object):
    def __init__(self):
        self.type = None
        self.complete = False
        self.elements = []
        self.data = None

    def __str__(self):
        pass

    def __bytes__(self):
        pass


class Element(object):
    pass


class Frame(object):
    pass