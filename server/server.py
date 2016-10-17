from chatease import Server, Stream, WebSocketStream, Cluster

server = Server(host="0.0.0.0", stream_cls=Stream, port=7521, ws_stream_cls=WebSocketStream,
                ws_port=7523, cluster_cls=Cluster, debug=True)


@server.frame("message")
def handle_message_frame(frame):
    to = frame.params.get("to")
    client = server.clients.get(to)
    if client:
        client.get("stream").write(bytes(frame))

@server.message("login")
def handle_login_message(message):
    username = message.params.get("username")
    password = message.params.get("password")
    if username == "ZhangSan" and password == "123456":
        server.clients["ZhangSan"] = {
            "stream": message.stream
        }
        print("ZhangSan Login")
        return True
    if username == "LiSi" and password == "654321":
        server.clients["LiSi"] = {
            "stream": message.stream
        }
        print("LiSi Login")
        return True
    return False


@server.message("message")
def handle_message_message(message):
    print(message.__dict__)

server.run()