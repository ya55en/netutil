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
TCP-based "ping" utility.

Makes successive tries to opens a TCP connection to a specified host + port
and reports the outcome in a fashion similar to the famous icmp `ping`.

See "./tcpping -h" for usage info.

The original source is maintained as part of `netutil` package at
  https://github.com/yassen-itlabs/netutil


TODO:
- Implement -q, -V options
- Add support for IPv6 addresses
- Add support + tests for python3

"""

from __future__ import print_function

import sys
import time
import socket
import argparse
from timeit import default_timer as wall_time


__version__ = '0.1.1'

DEFAULT_MAX_COUNT = 1000
DEFAULT_INTERVAL = 1.0
SOCKET_TIMEOUT = 1.0
DOT = '.'

HEADER_TMPL = '''TCPPING {} ({}) TCP SYN/ACK/close'''

FOOTER_TMPL = '''
--- {ipaddr} tcpping statistics ---
{total} connections attempted, {passed} established, {percent:d}% failed, time {totaltime}ms
rtt min/avg/max/mdev = {min:.3f}/{max:.3f}/{avg:.3f}/{mdev:.3f} ms
'''


def typeof(obj):
    return type(obj).__name__


class suppress(object):
    """Poor mans's contextlib.suppress() for python2."""
    def __init__(self, *exctypes):
        self._exctypes = exctypes
    def __enter__(self):
        return self
    def __exit__(self, typ, val, tb):
        if typ in self._exctypes:
            return True
        return None  # explicitly


def statistics(numbers):
    """Return a four-element tuple with following statistics:
    (min, max, avg, mdev) where mdev is the mean deviation.

    :param numbers: list - a list of floats
    :return: tuple
    """

    def mean(numbers):
        return float(sum(numbers)) / max(len(numbers), 1)

    avg = mean(numbers)
    mean_deviation = mean([abs(el - avg) for el in numbers])
    return min(numbers), max(numbers), avg, mean_deviation


def is_valid_ipv4(addr):
    """Return `True` iff given string is a valid IPv4 address.
    :param addr: str - the IP address (e.g. '127.0.0.1')
    :return: bool
    """
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False


def tcp_ping(host, port):
    """Try opening a TCP connection ('tcp-ping'). Return `True` on success
    and `False` on failure.

    :param host: str - the host to try opening connections to
    :param port: int - the TCP port to try opening connections to
    :return:
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOCKET_TIMEOUT)
    start = wall_time()  # measure wall time, always

    try:
        sock.connect((host, port))

    except socket.timeout:
        print("Connection timed out")
        return False, wall_time() - start

    except OSError as err:
        print("OSError:", str(err))
        return False, wall_time() - start

    except Exception as err:
        print("Exception occurred: ", typeof(err), ": ", str(err), sep="")
        return False

    else:
        return True, wall_time() - start

    finally:
        with suppress(Exception):
            sock.shutdown(socket.SHUT_RDWR)
        with suppress(Exception):
            sock.close()


def get_hostname_ipaddr(args):
    """Return a two-element tuple (hostname, ipv4addr) which ideally contain
    the DNS name and the IPv4 address of the host. In case `args.numeric_only`
    is `True` and the IPv4 address is given in args.host, then no attempt will
    be made to reverse-resolve the IP to a host name and the tuple is going to
    contain the ip address twice.

    :param args: Namespace - parsed command line arguments to the tcpping tool
    :return: tuple - (hostname, ipv4addr)
    """
    host = args.host
    hostname = None
    ipaddr = None

    if is_valid_ipv4(host):
        ipaddr = hostname = host
        if not args.numeric_only:
            hostname = socket.gethostbyaddr(ipaddr)[0]

    else:  # host contains hostname
        hostname = host
        ipaddr = socket.gethostbyname(hostname)

    return hostname, ipaddr


def do_loop(args, ipaddr):
    """Do the loop of repeating connection attempts gathering outcome data
    and return a three-element tuple `(passed: int, failed:int, times_list: list)`
    where `passed` and `failed` are counts of successful and unsuccessful
    connection attempts respectively, and `times_list` is a list of floats
    representing response times in seconds for each successful attempt.

    :param args: Namespace - parsed command line arguments to the tcpping tool
    :param ipaddr: str - the host ipv4 address
    :return: tuple
    """
    host, port, count = args.host, args.port, args.count
    passed = 0
    failed = 0
    times_list = list()

    try:
        for idx in xrange(count):
            isok, timespan = tcp_ping(ipaddr, port)
            passed += int(isok)
            failed += int(not isok)
            if isok:
                times_list.append(timespan)
                msg = "TCP/ACK from {}[{}]: tcp_seq={} time={:.3f} ms" \
                      .format(ipaddr, port, idx+1, 1000.0 * timespan)
                print(msg)
            if idx + 1 < count:
                time.sleep(args.interval)

        return (passed, failed, times_list)

    except KeyboardInterrupt:
        return (passed, failed, times_list)


def header(args):
    """Return the header template with host name and address interpolated.
    :param args: Namespace - parsed command line arguments to the tcpping tool
    :return: str
    """
    return HEADER_TMPL.format(*get_hostname_ipaddr(args))


def footer(*args):
    """Return the footer template with all data interpolated.
    :param args: list - a list of all arguments; see implementation
    :return: str
    """
    passed, failed, times_list, totaltime, hostname, ipaddr = args
    total = passed + failed
    percent = int(round(100.0 * failed / total))
    totaltime = int(round(totaltime * 1000.0))
    min, max, avg, mdev = [(elem * 1000.0) for elem in statistics(times_list)]
    return FOOTER_TMPL.format(**locals())


def parse_args(argv):
    """Parse the command line and return a Namespace containing the result.
    :param argv: list - command line arguments list
    :return: Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('host', metavar='destination', type=str, help="destination host name or IP address")
    parser.add_argument('port', metavar='port', type=int, help="destination tcp port")
    parser.add_argument('-c', metavar='count', dest='count', type=int, default=DEFAULT_MAX_COUNT,
                        help="Stop after making count SYN/ACK attempts (default: %(default)s)")
    parser.add_argument('-i', metavar='interval', dest='interval', type=float, default=DEFAULT_INTERVAL,
                        help="Wait interval seconds between attempting connection; "
                             "default is %(default)ss; cannot be less than 0.2s")
    parser.add_argument('-n', dest='numeric_only', action='store_true',
                        help="Numeric output only. No attempt will be made "
                             "to lookup symbolic names for host addresses.")
    args = parser.parse_args(argv)
    if args.interval < 0.2:
        args.interval = 0.2
        print("Warning: interval has been adjusted to 0.2s.")
    return args


def main(argv):
    """Do the job and return an int result code."""
    args = parse_args(argv)
    print(header(args))
    hostname, ipaddr = get_hostname_ipaddr(args)
    start_all = wall_time()
    try:
        results = list(do_loop(args, ipaddr))

    except Exception as exc:
        print("Unhandled Exception: {}: {}".format(typeof(exc), exc))
        return 9

    else:
        results.append(wall_time() - start_all)
        results.extend([hostname, ipaddr])
        print(footer(*results))
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
