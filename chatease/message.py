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
        self.mclass = ""

    def __len__(self):
        return len(self.data)

    @property
    def size(self):
        return len(self.data)


class WrapperMessage(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        if isinstance(self.data, str):
            return self.data
        if isinstance(self.data, dict):
            return json.dumps([e.dict() for e in self.data])

    def __bytes__(self):
        json.dumps(str(self)).encode("utf-8")


class TextMessage(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ExpressionMessage(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ImageMessage(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VoiceMessage(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class VideoMessage(MessageBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)