import asyncio


class Message(object):
    def __init__(self):
        self.type = None


class Messenger(asyncio.Protocol):
    def __init__(self, server):
        self.transport = None
        self.server = server
        self.buffer = bytes()
        self.parse_state = 1

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        pass

    def data_received(self, data):
        print(data)
        self.parse(data)

    def eof_received(self):
        pass

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass

    def parse(self, data):
        self.buffer += data
        if self.parse_state == 1:
            index = self.buffer.find(b"\n")
            if index != -1:
                line = self.buffer[:index]

    def handler_message(self, message):
        pass
