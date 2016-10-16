function MessageBase() {
    this.fr = "";
    this.to = "";
    this.data = new Uint8Array(0);
    this.size = 0;
    this.complete = false
}

function Message() {
}
Message.prototype = new MessageBase();

function WSFrame() {
    this.cmd = "";
    this.uuid = "";
    this.size = 0;
    this.seq = 0;
    this.nseqs = 0;
    this.params = {};
    this.data = new Uint8Array(0);

    this.toArrayBuffer = function () {
        this.size = this.data.length;
        var str = "CMD " + this.cmd + " " + this.uuid + " " + this.size + " " + this.seq + "/" + this.nseqs + "\r\n";

    }
}

function ChatClient(params) {
    this.url = params.url;
    this.protocol = params.protocol;
    this.websocket = null;
    this.filereader = new FileReader();
    this.buffer = new Uint8Array(0);

    this.messages = {};
    this.frame = new WSFrame();
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
                matches = line.match(/.*CMD +(\S+) +(\S+) +(\d+) +(\d+)\/(\d+)/);
                if (matches) {
                    self.frame.cmd = matches[1];
                    self.frame.uuid = matches[2];
                    self.frame.size = parseInt(matches[3]);
                    self.frame.seq = parseInt(matches[4]);
                    self.frame.nseqs = parseInt(matches[5]);
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
            if (self.buffer.length >= self.frame.size) {
                self.frame.data = self.buffer.slice(0, self.frame.size);
                self.buffer = self.buffer.slice(self.frame.size);
                self.onframe(self.frame);
                self.parse_state = "cmd";
                self.frame = new WSFrame();
                self.parse(new Uint8Array(0));
            }
        }
    };

    self.onframe = function (frame) {
        //console.log(frame);
        uuid = frame.uuid;
        nseqs = frame.nseqs;
        if (self.messages.hasOwnProperty(uuid)) {
            self.messages[uuid].push(frame);
        } else {
            self.messages[uuid] = [frame];
        }
        if (self.messages[uuid].length == nseqs) {
            message = new Message();
            message.fr = frame.params.from;
            message.to = frame.params.to;
            message.complete = true;
            self.messages[uuid].sort(function (a, b) {
                return a.seq - b.seq;
            });
            self.messages[uuid].forEach(function (frame) {
                buffer = new Uint8Array(message.data.length + frame.data.length);
                buffer.set(message.data);
                buffer.set(frame.data, message.data.length);
                message.data = buffer;
                message.size = buffer.length;
            });
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