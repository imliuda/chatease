import json


class MessageBase(object):
    def __init__(self, fr="", to="", data=None):
        """Message is a high level user message.

        :param str fr: where message comes from
        :param str to: where message should be sent to
        :param object data: the message data"""

        self.fr = fr
        self.to = to
        self.data = data
        self.size = 0
        self.complete = False


class Message(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        if isinstance(self.data, str):
            return self.data
        if isinstance(self.data, dict):
            return json.dumps([e.dict() for e in self.data])

    def __bytes__(self):
        json.dumps(str(self)).encode("utf-8")


class Expression(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Image(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Voice(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Video(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)