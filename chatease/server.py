import asyncio
from .stream import StreamMessage

class Server(object):
    def __init__(self, host="0.0.0.0", stream_cls=None, port=7521, ws_stream_cls = None,
                 ws_port=7523, cluster_cls=None, cluster_port=7581, broker_port=7591, debug=False):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(debug)
        self.host = host
        self.stream_cls = stream_cls
        self.port = port
        self.ws_stream_cls = ws_stream_cls
        self.ws_port = ws_port
        self.cluster = cluster_cls()
        self.cluster_port = cluster_port
        self.broker_port = broker_port
        self.brokers = []
        self.settings = {}
        # clients is a dict, it's structure as follow:
        # {
        #     "uid": {
        #         "stream": stream.Stream
        #     }
        # }
        self.clients = {}
        self.msgs = {}
        self.callbacks = {
            "frame": {},
            "message": {}
        }
        self.messages = asyncio.Queue()
        self.frames = asyncio.Queue()

    def message(self, cmd):
        def wrapper(func):
            self.callbacks["message"][cmd] = func
            def real(*args, **kwargs):
                func(*args, **kwargs)
            return real
        return wrapper

    def frame(self, cmd):
        def wrapper(func):
            self.callbacks["frame"][cmd] = func
            def real(*args, **kwargs):
                func(*args, **kwargs)
            return real
        return wrapper

    @asyncio.coroutine
    def handle_message_task(self):
        message_callbacks = self.callbacks.get("message")
        while True:
            message = yield from self.messages.get()
            callback = message_callbacks.get(message.cmd)
            if callback:
                self.loop.call_soon(callback, message)

    @asyncio.coroutine
    def handle_frame_task(self):
        frame_callbacks = self.callbacks.get("frame")
        while True:
            frame = yield from self.frames.get()
            callback = frame_callbacks.get(frame.cmd)
            if callback:
                self.loop.call_soon(callback, frame)
            self.loop.call_soon(self.handle_frame, frame)

    def handle_message(self, message):
        pass

    def handle_frame(self, frame):
        if "chunk" in frame.params:
            uuid = frame.params.get("uuid")
            nchunks = int(frame.params.get("chunk").split("/")[1].strip())
            if uuid in self.msgs:
                self.msgs[uuid].append(frame)
            else:
                self.msgs[uuid] = [frame]
            if len(self.msgs[uuid]) == nchunks:
                sorted(self.msgs[uuid], key=lambda x: x.params.get("chunk").split("/")[0].strip())
                message = StreamMessage()
                for frame in self.msgs[uuid]:
                    message.data += frame.data
                message.cmd = self.msgs[uuid][0].cmd
                message.params = self.msgs[uuid][0].params
                message.stream = frame.stream
                self.loop.create_task(self.messages.put(message))
                del self.msgs[uuid]
        else:
            message = StreamMessage()
            message.cmd = frame.cmd
            message.params = frame.params
            message.data = frame.data
            message.stream = frame.stream
            self.loop.create_task(self.messages.put(message))

    def run(self):
        # use create_task for version >= 3.4.2
        self.loop.create_task(self.handle_message_task())
        self.loop.create_task(self.handle_frame_task())
        coro = self.loop.create_server(
            protocol_factory=lambda: self.stream_cls(self),
            host=self.host,
            port=self.port,
        )
        self.loop.create_task(coro)
        coro = self.loop.create_server(
            protocol_factory = lambda: self.ws_stream_cls(self, paths=["/chat"], protocol="chat"),
            host=self.host,
            port=self.ws_port
        )
        self.loop.create_task(coro)
        self.loop.run_forever()
