import json


class Message(object):
    def __init__(self, data, fr="", to=""):
        """
        Message is a high level user message

        :param fr where message comes from
        :param to where message should be sent to
        :param elements a list of Element objects
        """
        self.fr = fr
        self.to = to
        assert isinstance(data, str) or isinstance(data, dict)
        self.data = data

    def __str__(self):
        if isinstance(self.data, str):
            return self.data
        if isinstance(self.data, dict):
            return json.dumps([e.dict() for e in self.data])

    def __bytes__(self):
        json.dumps(str(self)).encode("utf-8")


class Element(object):
    """
    Element stands for elements in a message, such as images, videos, voices, etc.
    """
    def __init__(self):
        self.type = ""
        self.fr = ""
        self.to = ""
        self.data = None

    def dict(self):
        return {}


class Frame(object):
    """
    Frame is a transfer entity in a socket stream.
    """
    def __init__(self):
        self.type = ""
        self.fr = ""
        self.to = ""
        self.size = 0
        self.checksum = None
        self.body = None