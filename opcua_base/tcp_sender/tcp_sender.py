import socket
import logging


class TCPSender:
    """
    Sends a TCP-Packet to the given ip-address. Currently used for sending a packets to the
    Homag BHX(program number which the machine should load)
    """
    @staticmethod
    def send_packet(tcp_packet, buffer_size=1024):
        _logger = logging.getLogger(__name__)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((tcp_packet.ip, tcp_packet.port))
            s.send(bytes(tcp_packet.message, 'utf-8'))
            # data = s.recv(buffer_size)
            s.close()
            # print("received data: ", data)
            return True
        except TimeoutError as e:
            _logger.error(
                'Could not send packet, host timed out. IP-address: {0}, port: {1}, message: {2}, error: {3}'.format(
                    tcp_packet.ip, tcp_packet.port, tcp_packet.message, e))
            return False


class TCPPacket:
    def __init__(self, ip, port, message):
        self.ip = ip
        self.port = port
        self.message = message
