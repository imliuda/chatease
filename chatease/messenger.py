import asyncio
import binascii
from .message import Message


class Messenger(asyncio.Protocol):
    """

    """
    parse_cmd = 1
    parse_params = 2
    parse_body = 3

    def __init__(self, server):
        self.transport = None
        self.server = server
        self.messages = asyncio.Queue(maxsize=200)
        self.buffer = bytearray()
        self.parse_state = self.parse_cmd

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
        if self.parse_state == self.parse_cmd:
            if self.buffer.find("\r\n") == -1:
                return
            if not self.buffer.startswith(b"CMD"):
                index = self.buffer.find(b"CMD")
                if index == -1:
                    self.buffer = bytearray()
                    return
                else:
                    self.buffer = self.buffer[index:]

            for index, c in enumerate(self.buffer):
                if c == "\n" and self._data[index - 1] == "\r":
                    line = self.buffer[self._cursor:index]

                    if line.strip().startswith("HIPC"):
                        tags = line.split(" ")
                        self._version = tags[0].strip().split("/")[1].strip()
                        self._type = tags[1].strip()
                        if self._type == "request":
                            self._resource = tags[2].strip()
                        elif self._type == "response" and len(tags) > 3:
                            self._dest = tags[2].strip()
                    else:
                        if self._cursor != index - 1:
                            pair = line.strip().split(":")
                            self._headers[pair[0].strip()] = pair[1].strip()
                        elif self._cursor == index - 1:
                            self._state = "header_found"
                            self._cursor = index + 1
                            break;
                    self._cursor = index + 1

        if self._state == "header_found":
            length = int(self.get_header("length"))
            checksum = int(self.get_header("checksum"))
            print(length, checksum)
            assert (length and checksum)
            if len(self._data) - self._cursor >= length:
                self._body = self._data[self._cursor:self._cursor + length]
                sum = binascii.crc32(self._body.encode("utf-8"))
                if sum != checksum:
                    self._data = self._data[4:]
                    self.parse(bytes())
                else:
                    self._state = "finished"
                    self._protocol.handle_ipc(self)

                    if len(self._data) - self._cursor > length:
                        self.get_ready()
                        self.parse(bytes())
                    else:
                        self.get_ready()
        return []

    def handle_message(self, message):
        callback = self.server.messenger_callbacks.get(message.type)
        if callback:
            data = callback(message)
            if isinstance(data, str):
                self.transport.write(data.encode("utf-8"))
