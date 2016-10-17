function StreamMessage(cmd, params, data) {
    this.cmd = cmd != undefined ? cmd : "";
    this.params = params != undefined ? params : {};
    this.data = data != undefined ? data : new Uint8Array(0);
}

function StreamFrame() {
    this.cmd = "";
    this.params = {};
    this.data = new Uint8Array(0);
}

function TextMessage(to, text) {
    this.cmd = "message";
    this.params.class = "text";
    this.params.to = to;
    this.data = new Uint8Array(text.length);
    for (var i=0; i<text.length; i++) {
        this.data[i] = text.charCodeAt(i);
    }

    this.toArrayBuffer = function () {
        var str = "CMD " + this.cmd + "\r\n";
        this.params.size = this.data.length;
        for (var p in this.params) {
            str += p + ": " + this.params[p] + "\r\n";
        }
        str += "\r\n";
        hb = new Uint8Array(str.length);
        for (var i=0; i<hb.length; i++) {
            hb[i] = str.charCodeAt(i);
        }
        buffer = new Uint8Array(str.length + this.data.length);
        buffer.set(hb);
        buffer.set(this.data, hb.length);
        return buffer;
    }
}
TextMessage.prototype = new StreamMessage();

function LoginMessage(username, password) {
    this.cmd = "login";
    this.params = {};
    this.params.username = username;
    this.params.password = password;

    this.toArrayBuffer = function () {
        var str = "CMD " + this.cmd + "\r\n";
        this.params.size = 0;
        for (var p in this.params) {
            str += p + ": " + this.params[p] + "\r\n";
        }
        str += "\r\n";
        hb = new Uint8Array(str.length);
        for (var i=0; i<hb.length; i++) {
            hb[i] = str.charCodeAt(i);
        }
        return hb;
    }
}

function ChatClient(params) {
    this.url = params.url;
    this.protocol = params.protocol;
    this.websocket = null;
    this.filereader = new FileReader();
    this.buffer = new Uint8Array(0);

    this.messages = {};
    this.frame = new StreamFrame();
    this.blobs = [];
    this.parse_state = "cmd";

    var self = this;

    this.connect = function () {
        this.websocket = new WebSocket(this.url, this.protocol);
        this.websocket.onopen = this.onopen;
        this.websocket.onclose = this.onclose;
        this.websocket.onmessage = this.onmessage;
        this.websocket.onerror = this.onerror;
        return this;
    };

    this.filereader.onload = function (event) {
        var arr = new Uint8Array(self.filereader.result);
        self.parse(arr);
        if (self.blobs.length > 0)
            self.readBlob();
    };

    this.readBlob = function () {
        if (self.filereader.readyState != FileReader.LOADING) {
            var blob = self.blobs.pop();
            if (blob) {
                self.filereader.readAsArrayBuffer(blob);
            }
        }
    };


    this.getLine = function () {
        // find "\r"
        var ri = self.buffer.indexOf(13);
        if (ri == -1)
            return false;
        // find "\n"
        var ni = self.buffer.indexOf(10, ri);
        if (ni != ri + 1) {
            self.buffer = self.buffer.slice(0, ri + 1);
            return false;
        }
        var line = self.buffer.slice(0, ri);
        self.buffer = self.buffer.slice(ri+2);
        return self.arrayToString(line);
    };

    this.arrayToString = function (array) {
        str = "";
        for (var i = 0; i < array.length; i++) {
            str += String.fromCharCode(array[i]);
        }
        return str;
    };

    this.parse = function (u8arr) {
        var buffer = new Uint8Array(self.buffer.length + u8arr.length);
        buffer.set(self.buffer, 0);
        buffer.set(u8arr, self.buffer.length);
        self.buffer = buffer;
        if (self.parse_state == "cmd") {
            var line = self.getLine();
            if (line) {
                matches = line.match(/.*CMD +(\S+).*/);
                if (matches) {
                    self.frame.cmd = matches[1];
                    self.parse_state = "headers";
                    //console.log(self.frame);
                }
            }
        }
        if (self.parse_state == "headers") {
            line = self.getLine();
            if (line != "") {
                matches = line.match(/\s*(\S+)\s*:\s*(\S+)\s*/);
                self.frame.params[matches[1]] = matches[2];
                self.parse(new Uint8Array(0));
                //console.log(self.frame.params);
            } else if (line == "") {
                self.parse_state = "data";
            }
        }
        if (self.parse_state == "data") {
            if (self.buffer.length >= self.frame.params.size) {
                self.frame.data = self.buffer.slice(0, self.frame.params.size);
                self.buffer = self.buffer.slice(self.frame.params.size);
                self.onframe(self.frame);
                self.parse_state = "cmd";
                self.frame = new StreamFrame();
                self.parse(new Uint8Array(0));
            }
        }
    };

    self.onMessageFrame = function (frame) {

    };

    self.onframe = function (frame) {
        //console.log(frame);
        var message;
        if (frame.params.hasOwnProperty("chunk")) {
            var uuid = frame.params.uuid;
            if (self.messages.hasOwnProperty(uuid)) {
                self.messages[uuid].push(frame)
            } else {
                self.messages[uuid] = [frame];
            }
            var nchunks = parseInt(frame.params.chunk.split("/")[1].trim());
            if (self.messages[uuid].length == nchunks) {

                self.messages[uuid].sort(function (a, b) {
                    return parseInt(a.params.chunk.split("/")[0]) - parseInt(b.params.chunk.split("/")[0]);
                });
                message = new StreamMessage();
                self.messages[uuid].forEach(function (frame) {
                    buffer = new Uint8Array(message.data.length + frame.data.length);
                    buffer.set(message.data);
                    buffer.set(frame.data, message.data.length);
                    message.data = buffer;
                });
                message.cmd = self.messages[uuid][0].cmd;
                message.params = self.messages[uuid][0].params;
                self.onChatMessage(message);
            }
        } else {
            message = new StreamMessage();
            message.cmd = frame.cmd;
            message.params = frame.params;
            message.data = frame.data;
            self.onChatMessage(message);
        }
    };

    self.onChatMessage = function (message) {
        console.log(message);
    };

    self.onConnected = function () {

    };

    self.onClose = function () {

    };

    self.onError = function () {

    };

    this.send = function (data) {
        if (this.websocket.readyState != WebSocket.OPEN)
            return;
        this.websocket.send(data);
    };


    /*********Bellow is websocket's method********/
    this.onopen = function () {
        self.onConnected();
    };

    this.onclose = function () {
        self.onClose();
    };

    this.onmessage = function (message) {
        self.blobs.push(message.data);
        if (self.filereader.readyState != FileReader.LOADING) {
            self.readBlob();
        }
    };

    this.onerror = function () {
        self.onError();
    };
}