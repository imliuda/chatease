import asyncio
import binascii


class StreamFrame(object):
    """
    Frame is a transfer entity in a socket stream.
    """
    def __init__(self):
        self.cmd = ""
        self.params = {}
        self.data = None

    def __bytes__(self):
        data = "CMD " + self.cmd + "\r\n"
        for p in self.params:
            data += p + ": " + self.params[p] + "\r\n"
        data += "\r\n"
        return data.encode("utf-8") + self.data


class StreamMessage(StreamFrame):
    pass


class StreamParser(object):
    parse_cmd = 1
    parse_params = 2
    parse_data = 3

    def __init__(self, stream):
        self.buffer = bytearray()
        self.parse_state = self.parse_cmd
        self.frame = StreamFrame()
        self.on_frame = None
        self.stream = stream

    def parse(self, data):
        self.buffer += data
        if self.parse_state == self.parse_cmd:
            end_index = self.buffer.find(b"\r\n")
            if end_index == -1:
                return
            start_index = self.buffer.find(b"CMD")
            if start_index == -1:
                self.buffer = bytearray()
                return
            else:
                line = self.buffer[start_index:end_index]
                self.buffer = self.buffer[end_index + 2:]
                cmds = line.split(b" ")
                if len(cmds) != 2:
                    return
                self.frame.cmd = cmds[1].decode("ascii")
                self.parse_state = self.parse_params

        if self.parse_state == self.parse_params:
            index = self.buffer.find(b"\r\n")
            if index == -1:
                return
            line = self.buffer[:index]
            self.buffer = self.buffer[index + 2:]
            if line:
                name, colon, value = line.partition(b":")
                if colon == b":":
                    self.frame.params[name.decode("ascii").strip()] = value.decode("ascii").strip()
                if self.buffer:
                    self.parse(bytearray())
            else:
                self.parse_state = self.parse_data

        if self.parse_state == self.parse_data:
            if len(self.buffer) >= int(self.frame.params["size"]):
                self.frame.data = self.buffer[:int(self.frame.params["size"])]
                self.frame.stream = self.stream
                if self.on_frame:
                    self.on_frame(self.frame)
                self.frame = StreamFrame()
                self.parse_state = self.parse_cmd
                self.parse(bytearray())


class Stream(asyncio.Protocol):
    def __init__(self, server):
        self.transport = None
        self.server = server
        self.parser = StreamParser(self)
        self.parser.on_frame = self.on_frame

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        pass

    def data_received(self, data):
        self.parser.parse(data)

    def eof_received(self):
        pass

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass

    def on_frame(self, frame):
        frame.stream = self
        self.server.loop.create_task(self.server.frames.put(frame))

    def write(self, data):
        self.transport.write(data)