from chatease import Server, Messenger

app = Server(Messenger)

@app.messenger_handler("login")
def handle_login(message):
    return "fffffffff"

if __name__ == "__main__":
    app.run()