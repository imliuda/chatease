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
        self.clients = []
        self.messages = asyncio.Queue()
        self.frames = asyncio.Queue()

    @asyncio.coroutine
    def handle_message_task(self):
        while True:
            messenge = yield from self.messages.get()
            self.handle_message(messenge)

    @asyncio.coroutine
    def handle_frames_task(self):
        while True:
            frame = yield from self.frames.get()
            self.handle_frames(frame)

    def handle_message(self, message):
        pass

    def handle_frames(self, frame):
        print(frame.__dict__)

    def run(self):
        asyncio.ensure_future(self.handle_message_task())
        asyncio.ensure_future(self.handle_frames_task())
        coro = self.loop.create_server(
            protocol_factory=lambda: self.stream_cls(self),
            host=self.host,
            port=self.port,
        )
        asyncio.ensure_future(coro)
        self.loop.run_forever()
