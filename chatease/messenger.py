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
        messages = self.parse(data)
        for message in messages:
            self.handle_message(message)

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
        return []

    def handle_message(self, message):
        callback = self.server.messenger_callbacks.get(message.type)
        if callback:
            data = callback(message)
            if isinstance(data, str):
                self.transport.write(data.encode("utf-8"))
