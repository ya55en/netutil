#! /usr/bin/env python

# Distributed under the MIT license.
# Copyright (c) 2019 Yassen Damyanov <yd@itlabs.bg>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Simple TCP socket echo server. Repeats back what has been sent over the wire.

The original source is maintained as part of `netutil` package at
  https://github.com/yassen-itlabs/netutil

"""
from __future__ import print_function

import sys
import socket
import argparse


DEFAULT_BIND_HOST = '0.0.0.0'
DEFAULT_BIND_PORT = 65432
SOCKET_BUF_SIZE = 1024
SOCKET_BACKLOG = 5


def typeof(obj):
    return type(obj).__name__


def start(host, port):
    """Create server socket and start listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))

    except socket.error as err:
        print("E: Bind failed: [Errno {0}] {1}".format(*err[0:2]))
        sys.exit(2)

    try:
        sock.listen(SOCKET_BACKLOG)
        print("Echo Server (TCP) listening on {} port {}...".format(host, port))
        while True:
            try:
                conn, addr = sock.accept()  # blocks waiting for a client to connect
                print("* Client {0}:{1} connected".format(*addr[0:2]))
                conn.send("Say something:\n> ")
                reply = conn.recv(SOCKET_BUF_SIZE).rstrip()
                if reply:
                    print("Client said:", reply)
                conn.send("You said: {}\n".format(reply))
                conn.close()

            except socket.error as err:
                print("{}: {}".format(typeof(err), err))

    except Exception as err:
        print("E: Unexpected: {}: {}".format(typeof(err), err))
        sys.exit(2)


def parse_args(argv):
    """Parse the command line and return a Namespace containing the result.
    :param argv: list - command line arguments list
    :return: Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bind', metavar='BIND-ADDR', type=str, default=DEFAULT_BIND_HOST,
                        help="host/address to bind to (default: %(default)s)")
    parser.add_argument('-p', '--port', metavar='BIND-PORT', type=int, default=DEFAULT_BIND_PORT,
                        help="TCP port to bind to (default: %(default)s)")
    args = parser.parse_args(argv)
    return args


def main(argv):
    args = parse_args(argv)
    try:
        start(args.bind, args.port)
    except KeyboardInterrupt:
        print(" Canceled by user")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
