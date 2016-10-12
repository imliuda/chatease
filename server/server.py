from chatease import Server, Stream

app = Server(Stream, host="0.0.0.0", port=7521, cluster=None, debug=True)

if __name__ == "__main__":
    app.run()