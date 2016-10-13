from chatease import Server, Stream


class ChatServer(Server):
    def handle_frame(self, frame):
        to = frame.params.get("to")
        user = self.clients.get(to)
        if user:
            # if destination is also in this server
            stream = user.get("stream")
            stream.write(bytes(frame))
        # try to get user information from cluster server
        else:
            address = self.cluster.get_user_server(to)
            if address:
                pass

if __name__ == "__main__":
    server = Server(Stream, host="0.0.0.0", port=7521, cluster=None, debug=True)
    server.run()