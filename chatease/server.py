import asyncio

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
        #     "user_id": {
        #         "stream": stream.Stream
        #     }
        # }
        self.clients = {}
        self.messages = asyncio.Queue()
        self.frames = asyncio.Queue()

    @asyncio.coroutine
    def handle_message_task(self):
        while True:
            message = yield from self.messages.get()
            self.loop.call_soon(self.handle_message, message)

    @asyncio.coroutine
    def handle_frame_task(self):
        while True:
            frame = yield from self.frames.get()
            self.loop.call_soon(self.handle_frame, frame)

    def handle_message(self, message):
        pass

    def handle_frame(self, frame):
        pass

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
