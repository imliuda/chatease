import asyncio
import binascii
from .message import Message


class StreamFrame(object):
    """
    Frame is a transfer entity in a socket stream.
    """
    def __init__(self):
        self.cmd = ""
        self.uuid = ""
        self.size = 0
        self.seq = 0
        self.nseqs = 0
        self.params = {}
        self.data = None


class StreamParser(object):
    parse_cmd = 1
    parse_params = 2
    parse_data = 3

    def __init__(self):
        self.buffer = bytearray()
        self.parse_state = self.parse_cmd
        self.frame = StreamFrame()
        self.on_frame = None

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
                if len(cmds) != 5:
                    return
                # the format of cmd line is as follow:
                # CMD login bf997e18-8f07-11e6-b1b1-b46d8361714b 4885 1/5
                self.frame.cmd = cmds[1]
                self.frame.uuid = cmds[2]
                self.frame.size = int(cmds[3])
                self.frame.seq = int(cmds[4].split(b"/")[0])
                self.frame.nseqs = int(cmds[4].split(b"/")[1])
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
            if len(self.buffer) >= self.frame.size:
                self.frame.data = self.buffer[:self.frame.size]
                if self.on_frame:
                    self.on_frame(self.frame)
                self.frame = StreamFrame()
                self.parse_state = self.parse_cmd
                self.parse(bytearray())


class Stream(asyncio.Protocol):
    def __init__(self, server):
        self.transport = None
        self.server = server
        self.parser = StreamParser()
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
        self.server.loop.create_task(self.server.frames.put(frame))

    def write(self, data):
        self.transport.write(data)