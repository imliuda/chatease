import asyncio
from . import messenger


class Server(object):
    def __init__(self, messenger_class, messenger_host="0.0.0.0", messenger_port=7521,  broker_class=None, cluster_class=None):
        self.loop = asyncio.get_event_loop()
        self.messenger_class = messenger_class
        self.messenger_host = messenger_host
        self.messenger_port = messenger_port
        self.broker_class = broker_class
        self.cluster_class = cluster_class
        self.messenger = None
        self.brokers = []
        self.clusters = []
        self.users = []

    def run(self):
        coro = self.loop.create_server(lambda: self.messenger_class(self), self.messenger_host, self.messenger_port)
        self.messenger = self.loop.run_until_complete(coro)
        self.loop.run_forever()


if __name__ == "__main__":
    server = Server(messenger.Messenger)
    server.run()