import json


class Message(object):
    def __init__(self, data, fr="", to=""):
        """
        Message is a high level user message

        :param fr where message comes from
        :param to where message should be sent to
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
