import asyncio
import struct
import logging
import hashlib
import base64
from enum import IntEnum
from urllib.parse import urlparse
from .stream import StreamParser

logger = logging.getLogger(__name__)


class WSMessageType(IntEnum):
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xa


class WSMessage(object):
    def __init__(self):
        self.type = None
        self.data = bytearray()


class WSFrame(object):
    def __init__(self):
        self.fin = 0
        self.rsv = 0
        self.opcode = 0
        self.mask = 0
        self.len = 0
        self.key = []
        self.payload = None

    def __bytes__(self):
        data = bytearray()
        data.append((self.fin << 7) | (self.rsv << 3) | self.opcode)
        length = len(self.payload)
        if length < 126:
            data.append(self.mask | length)
        elif 127 < length <= 2**16:
            data.append(self.mask | 126)
            data += struct.pack("!H", length)
        elif 2**16 < length < 2**64:
            data.append(self.mask | 127)
            data += struct.pack("!Q", length)
        if self.mask:
            pass
        data += self.payload
        return bytes(data)


class WebSocketStream(asyncio.Protocol):
    parse_http_request = 1
    parse_http_header = 2
    parse_ws_byte1 = 3
    parse_ws_byte2 = 4
    parse_ws_len2 = 8
    parse_ws_len8 = 9
    parse_ws_key = 10
    parse_ws_payload = 11
    accept_key = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    frame_size = 8192

    def __init__(self, server, paths=(), protocol="chat", extensions=()):
        self.transport = None
        self.server = server
        self.buffer = bytearray()
        self.headers = {}
        self.ws_message = None
        self.ws_frame = WSFrame()
        self.parse_state = self.parse_http_request
        self.stream_parser = StreamParser(self)
        self.stream_parser.on_frame = self.on_frame

        self.path = ""
        self.paths = paths
        self.protocol = protocol
        self.extension = ""
        self.extensions = extensions
        self.ws_key = ""
        self.host = ""
        self.origin = ""

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.parse_data(data)

    def parse_data(self, data):
        self.buffer += data
        if self.parse_state == self.parse_http_request:
            index = self.buffer.find(b"\r\n")
            if index == -1:
                return
            line = self.buffer[:index]
            self.buffer = self.buffer[index + 2:]
            reqs = line.split()
            if reqs[0] != b"GET" or reqs[2] != b"HTTP/1.1":
                self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
                self.transport.close()
            self.path = urlparse(reqs[1]).path.decode("utf-8")
            self.parse_state = self.parse_http_header

        if self.parse_state == self.parse_http_header:
            index = self.buffer.find(b"\r\n")
            if index == -1:
                return
            line = self.buffer[:index]
            self.buffer = self.buffer[index + 2:]
            if line:
                name, colon, value = line.partition(b":")
                if colon == b":":
                    self.headers[name.decode("utf-8").strip()] = value.decode("utf-8").strip()
                self.parse_data(bytearray())
            else:
                if self.opening_ws_handshake():
                    self.parse_state = self.parse_ws_byte1
                else:
                    self.transport.close()

        if self.parse_state == self.parse_ws_byte1:
            if len(self.buffer) < 1:
                return
            b = self.buffer[0]
            self.buffer = self.buffer[1:]
            self.ws_frame.fin = (b >> 7) & 0b1
            self.ws_frame.rsv = (b >> 4) & 0b111
            self.ws_frame.opcode = b & 0b1111
            self.parse_state = self.parse_ws_byte2

        if self.parse_state == self.parse_ws_byte2:
            if len(self.buffer) < 1:
                return
            b = self.buffer[0]
            self.buffer = self.buffer[1:]
            self.ws_frame.mask = (b >> 7) & 0b1
            length = b & 0b1111111
            if length < 126:
                self.ws_frame.len = length
                self.parse_state = self.parse_ws_key
            elif length == 126:
                self.parse_state = self.parse_ws_len2
            elif length == 127:
                self.parse_state = self.parse_ws_len8

        if self.parse_state == self.parse_ws_len2:
            if len(self.buffer) < 2:
                return
            lengths = self.buffer[:2]
            self.buffer = self.buffer[2:]
            self.ws_frame.len = struct.unpack("!H", lengths)[0]
            self.parse_state = self.parse_ws_key

        if self.parse_state == self.parse_ws_len8:
            if len(self.buffer) < 8:
                return
            lengths = self.buffer[:8]
            self.buffer = self.buffer[8:]
            self.ws_frame.len = struct.unpack("!Q", lengths)[0]
            self.parse_state = self.parse_ws_key

        if self.parse_state == self.parse_ws_key:
            if self.ws_frame.mask:
                if len(self.buffer) < 4:
                    return
                self.ws_frame.key = self.buffer[:4]
                self.buffer = self.buffer[4:]
                self.parse_state = self.parse_ws_payload
            else:
                self.parse_state = self.parse_ws_payload

        if self.parse_state == self.parse_ws_payload:
            if len(self.buffer) >= self.ws_frame.len:
                self.ws_frame.payload = self.buffer[:self.ws_frame.len]
                self.buffer = self.buffer[self.ws_frame.len:]
                self.handle_ws_frame(self.ws_frame)
                self.ws_frame = WSFrame()
                self.parse_state = self.parse_ws_byte1
                self.parse_data(bytearray())

    def fail_connection(self):
        pass

    def opening_ws_handshake(self):
        if self.path not in self.paths:
            self.transport.write(b"HTTP/1.1 404 Not Found\r\n")
            return False
        fields = {}
        for field in self.headers:
            fields[field.lower()] = self.headers[field]
        if "host" not in fields:
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False
        if "upgrade" not in fields:
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False
        upgrades = [x.strip().lower() for x in fields["upgrade"].split(",")]
        if "websocket" not in upgrades:
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False
        if "connection" not in fields:
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False
        connections = [x.strip().lower() for x in fields["connection"].split(",")]
        if "upgrade" not in connections:
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False
        if "sec-websocket-key" not in fields:
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False
        if "sec-websocket-version" not in fields:
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False
        if fields["sec-websocket-version"] != "13":
            self.transport.write(b"HTTP/1.1 400 Bad Request\r\n")
            return False

        self.host = fields["host"]
        self.ws_key = fields["sec-websocket-key"]
        if "origin" in fields:
            self.origin = fields["origin"]
        if "sec-websocket-protocol" in fields:
            protocols = [x.strip() for x in fields["sec-websocket-protocol"].split(",")]
            if self.protocol not in protocols:
                self.protocol = ""

        if "sec-websocket-extensions" in fields:
            pass

        sha1 = hashlib.sha1((self.ws_key + self.accept_key).encode("utf-8")).digest()
        key = base64.standard_b64encode(sha1)
        resp = b"HTTP/1.1 101 Switching Protocols\r\n" \
               b"Upgrade: websocket\r\n" \
               b"Connection: Upgrade\r\n" \
               b"Sec-WebSocket-Accept: " + key + b"\r\n"
        if "sec-websocket-protocol" in fields and self.protocol:
            resp += b"Sec-WebSocket-Protocol: " + self.protocol.encode("utf-8") + b"\r\n"
        resp += b"\r\n"
        self.transport.write(resp)
        self.write(b"CMD message 5 1/2\r\n"
                   b"class: text\r\n"
                   b"uuid: 2a4fd4a4-9373-11e6-b1b1-b46d8361714b\r\n"
                   b"size: 5\r\n"
                   b"chunk: 1/2\r\n"
                   b"from: hello\r\n"
                   b"type: text/plain\r\n\r\nabcde")
        self.write(b"fwfwefwCMD message\r\n"
                   b"class: text\r\n"
                   b"uuid: 2a4fd4a4-9373-11e6-b1b1-b46d8361714b\r\n"
                   b"size: 5\r\n"
                   b"chunk: 2/2\r\n"
                   b"from: hello\r\n"
                   b"type: text/plain\r\n\r\nqqqqq")
        return True

    def mask_payload(self, data):
        for i in range(len(data)):
            j = i % 4
            data[i] = data[i] ^ self.ws_frame.key[j]
        return data

    def handle_ws_frame(self, frame):
        """
        handle websocket frame
        when message type is text or binary, send it to parser
        todo confirm what message should send to parser
        """
        self.mask_payload(frame.payload)
        # print(frame.payload)
        if frame.fin == 0:
            if frame.opcode != 0:
                self.ws_message = WSMessage()
                self.ws_message.type = frame.opcode
            if frame.opcode == 0:
                self.ws_message.data += frame.payload
        if frame.fin == 1:
            if frame.opcode == 0:
                self.ws_message.data += frame.payload
                self.stream_parser.parse(self.ws_message.data)
            if frame.opcode == WSMessageType.BINARY.value:
                self.stream_parser.parse(frame.payload)
            if frame.opcode == WSMessageType.TEXT.value:
                # although it is websocket text message type, but it is still
                # in binary format javascript will automatically convert
                # String, ArrayBuffer, and other types to network bytes stream
                self.stream_parser.parse(frame.payload)
            if frame.opcode == WSMessageType.PING.value:
                self.on_ping(frame)
            if frame.opcode == WSMessageType.PONG.value:
                self.on_pong(frame)
            if frame.opcode == WSMessageType.CLOSE.value:
                self.on_close(frame)

    def ping(self):
        pass

    def pong(self):
        pass

    def on_ping(self, frame):
        """
        user can override this method to do ping
        """
        pass

    def on_pong(self, frame):
        """
        user can override this method to do pong
        """
        pass

    def on_close(self, frame):
        pass

    def on_frame(self, frame):
        """
        callback for StreamFrame
        """
        self.server.loop.create_task(self.server.frames.put(frame))

    def send_ws_frame(self, frame):
        self.transport.write(bytes(frame))

    def write(self, data):
        if len(data) <= self.frame_size:
            frame = WSFrame()
            frame.fin = 1
            frame.rsv = 0
            frame.opcode = WSMessageType.BINARY.value
            frame.mask = 0
            frame.payload = data
            self.send_ws_frame(frame)
        else:
            frame = WSFrame()
            frame.fin = 0
            frame.rsv = 0
            frame.opcode = WSMessageType.BINARY.value
            frame.mask = 0
            frame.payload = data[:self.frame_size]
            self.send_ws_frame(frame)
            data = data[self.frame_size:]
            nframes = len(data) // self.frame_size
            if len(data) % self.frame_size == 0:
                nframes -= 1
            for i in range(nframes):
                frame = WSFrame()
                frame.fin = 0
                frame.rsv = 0
                frame.opcode = 0
                frame.payload = data[:self.frame_size]
                self.send_ws_frame(frame)
                data = data[self.frame_size:]
            frame = WSFrame()
            frame.fin = 1
            frame.rsv = 0
            frame.opcode = 0
            frame.mask = 0
            frame.payload = data[:self.frame_size]
            self.send_ws_frame(frame)

    def write_text(self, data):
        """
        this function is the copy of write, just change the frame.opcode
        to Text type, i would not use this in this project. This is not well tested.
        """
        if len(data) <= self.frame_size:
            frame = WSFrame()
            frame.fin = 1
            frame.rsv = 0
            frame.opcode = WSMessageType.TEXT.value
            frame.mask = 0
            frame.payload = data
            self.send_ws_frame(frame)
        else:
            frame = WSFrame()
            frame.fin = 0
            frame.rsv = 0
            frame.opcode = WSMessageType.TEXT.value
            frame.mask = 0
            frame.payload = data[:self.frame_size]
            self.send_ws_frame(frame)
            data = data[self.frame_size:]
            nframes = len(data) // self.frame_size
            if len(data) % self.frame_size == 0:
                nframes -= 1
            for i in range(nframes):
                frame = WSFrame()
                frame.fin = 0
                frame.rsv = 0
                frame.opcode = 0
                frame.payload = data[:self.frame_size]
                self.send_ws_frame(frame)
                data = data[self.frame_size:]
            frame = WSFrame()
            frame.fin = 1
            frame.rsv = 0
            frame.opcode = 0
            frame.mask = 0
            frame.payload = data[:self.frame_size]
            self.send_ws_frame(frame)

    def close(self):
        self.transport.close()