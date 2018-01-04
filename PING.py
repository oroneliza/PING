#! /usr/bin/python
import os
import sys
import logging
import time
from socket import *
from optparse import OptionParser

log_file = os.getcwd() + '/PING.log'
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format= "%(asctime)-15s [%(name)s:%(lineno)s:%(funcName)s:%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(stdout_handler)


protocol_dict = {'UDP': SOCK_DGRAM,
                 'TCP': SOCK_STREAM}


def get_socket(state, protocol, address, port):
    try:
        sock = socket(AF_INET, protocol_dict[protocol])
        if state == 'client':
            pass
        else:
            sock.bind((address, port))
            if protocol == 'TCP':
                sock.listen(1)
        return sock
    except Exception as err:
        logger.error('{}'.format(str(err)))


def create_packet(packet_len):
    return 'D' * packet_len


class Server(object):

    def __init__(self, options):
        self.address = options.address
        self.port = int(options.port)
        self.protocol = options.protocol.upper()
        self.packet_size = int(options.packet_size)
        self.socket = get_socket('server', self.protocol, self.address, self.port)

    def start(self):
        logger.info('Starting {} server: \n    port: {}\n'.format(
                                    self.protocol, self.port))
        try:
            while True:
                if self.protocol == 'TCP':
                    connection, host_address = self.socket.accept()
                    data = connection.recv(self.packet_size)
                    connection.send(data)
                    connection.close()
                else:
                    data, host_address = self.socket.recvfrom(self.packet_size)
                    self.socket.sendto(data, host_address)
                logger.info('Received packet of {} bytes from address {}'.format(self.packet_size, self.address))
        finally:
            self.socket.close()


class Client(object):
    def __init__(self, options):
        self.protocol = options.protocol.upper()
        self.packet_size = int(options.packet_size)
        self.timeout = int(options.timeout)
        self.req_count = int(options.req_count)
        self.address = options.address
        self.port = int(options.port)
        self.socket = None

    def start(self):
        logger.info('Pinging {} with {} bytes of data:'.format(
                            self.address, self.packet_size))
        time_deltas = []
        received_pck = 0.0
        try:
            for index in xrange(self.req_count):
                start_time = time.time()
                self.socket = get_socket('client', self.protocol, self.address, self.port)
                self.socket.settimeout(self.timeout * 10e-3)
                try:
                    data = create_packet(self.packet_size)
                    if self.protocol == 'TCP':
                        self.socket.connect((self.address, self.port))
                        self.socket.send(data)
                    else:
                        self.socket.sendto(data, (self.address, self.port))
                    data = self.socket.recv(self.packet_size)
                    received_pck += 1
                    end_time = time.time()
                    delta = int((end_time - start_time) * 1000)
                    logger.info('    Replay from {}: bytes={} time={}ms TTL={}'.format(self.address, self.packet_size,
                                                                               '<1' if delta < 1 else str(delta), self.timeout))
                    time_deltas.append(delta)
                except timeout:
                    logger.info('    Request time out')
		finally:
                    self.socket.close()
        finally:
            if time_deltas:
                pck_loss = int(100 - (100 * (received_pck / self.req_count)))
                logger.info('\nPing statistics for {}:\n    Packets: Sent = {}, Received = {}, Lost = {} ({}% loss)'.format(
                    self.address, self.req_count, len(time_deltas), self.req_count - len(time_deltas), pck_loss))
                logger.info('Approximate round trip times in milli-seconds:\n    Minimum = {}ms, Maximum = {}ms, Avarage = {}ms\n'.format(
                    min(time_deltas), max(time_deltas), sum(time_deltas) / len(time_deltas)))


def main():
    parser = OptionParser(usage="usage: %prog [options] filename",
                          version="%prog 1.0")

    parser.add_option("--mode",
                      dest='mode',
                      default='client',
                      help="Set state mode. client/server")

    parser.add_option("--protocol",
                      dest='protocol',
                      default='UDP',
                      help="Choose which network protocol to use UDP/TCP")

    parser.add_option("--timeout",
                      dest='timeout',
                      default=128,
                      help="Set request timeout in seconds")

    parser.add_option("--req-count",
                      dest='req_count',
                      default=4,
                      help="Number of echo requests to send")

    parser.add_option("--pck-size",
                      dest='packet_size',
                      default=32,
                      help="Set packet size in bytes")

    parser.add_option("--address",
                      dest='address',
                      default='127.0.0.1',
                      help="Set host address")

    parser.add_option("--port",
                      dest='port',
                      default=1521,
                      help="Set host port")

    (options, args) = parser.parse_args()

    if options.mode == 'client':
        host = Client(options)
    else:
        host = Server(options)
    host.start()

if __name__ == '__main__':
    main()
