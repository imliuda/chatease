from chatease import Server, Stream, WebSocketStream, Cluster


class ChatServer(Server):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def handle_frame(self, frame):
        print(frame.__dict__)
        to = frame.params.get("to")
        user = self.clients.get(to)
        # if destination is also in this server
        if user:
            stream = user.get("stream")
            stream.write(bytes(frame))
        # try to get user information from cluster server
        else:
            address = self.cluster.get_user_server(to)
            if address:
                pass

if __name__ == "__main__":
    server = ChatServer(host="0.0.0.0", stream_cls=Stream, port=7521, ws_stream_cls=WebSocketStream,
                        ws_port=7523, cluster_cls=Cluster, debug=True)
    server.run()