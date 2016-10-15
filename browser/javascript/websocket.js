function ChatClient(params) {
    this.url = params.url;
    this.protocol = params.protocol;
    this.websocket = null;

    this.connect = function () {
        this.websocket = new WebSocket(this.url, this.protocol);
        this.websocket.onopen = this.onopen;
        this.websocket.onclose = this.onclose;
        this.websocket.onmessage = this.onmessage;
        this.websocket.onerror = this.onerror;
        return this;
    };

    this.onopen = function () {
    };

    this.onclose = function () {

    };

    this.onmessage = function (message) {
        reader = new FileReader();
        reader.onload = function (event) {
            //alert(reader.result);
        };
        //reader.readAsBinaryString(message.data);
        console.log(message.data.length)
    };

    this.onerror = function (message) {
    };

    this.sendBinary = function (data) {
        if (this.websocket.readyState != WebSocket.OPEN)
            return;
        this.websocket.send(data);
    }
}