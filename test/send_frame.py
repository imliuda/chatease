#!/usr/bin/env python3

import socket

import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.connect(("127.0.0.1", 7521))
sock.send(b"CMD message bf997e18-8f07-11e6-b1b1-b46d8361714b 0 2/4\r\n\r\ntype")
while True:
    sock.send(b"CMD message bf997e18-8f07-11e6-b1b1-b46d8361714b 14 2/4\r\n"
              b"type: image/jpeg\r\n"
              b"from: zhangsan\r\n"
              b"\r\n"
              b"i am a message")

    time.sleep(1)