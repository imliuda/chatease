import asyncio


class Server(object):
    def __init__(self, stream_cls, host="0.0.0.0", port=7521, cluster=None, debug=False):
        self.loop = asyncio.get_event_loop()
        self.loop.set_debug(debug)
        self.stream_cls = stream_cls
        self.host = host
        self.port = port
        self.cluster = cluster
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
        self.loop.run_forever()
