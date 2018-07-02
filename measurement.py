"""
The base test class implementing latency measurement-related functionality
common to all measurement types (i.e. sending packets and saving results to a
file).
"""

from __future__ import division
import socket
import time
import datetime
import argparse
import pickle
import sys

class Measurement:

    def __init__(self, test_output_filename):
        self.test_output_filename = test_output_filename

    @classmethod
    def send_packets(cls, target_address, n_packets, packet_len, send_rate_kbytes_per_s, output_filename, out_file):
        """
        Send n_packets packets, each with a payload of packet_len bytes, to
        target_address, trying to maintain a constant send rate of
        send_rate_kbytes_per_s.
        """
        send_rate_bytes_per_s = send_rate_kbytes_per_s * 1000
        packet_rate = send_rate_bytes_per_s / packet_len
        packet_interval = 1 / packet_rate

        sock_out = \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_out.connect(target_address)

        sock_out.settimeout(5)
        packets = []

        cls.pre_send(n_packets, sock_out)

        print("Sending %d %d-byte packets at about %d kB/s to %s:%d..." %
              (n_packets, packet_len, send_rate_kbytes_per_s, target_address[0],
               target_address[1]))

        send_start_seconds = time.time()
        inter_packet_sleep_times_ms = []
        if n_packets == 0:
            n_packets = sys.maxint
        #for packet_n in range(n_packets):
        for packet_n in xrange(n_packets):
            tx_start_seconds = time.time()

            payload = cls.get_packet_payload(packet_n)
            n_fill_bytes = packet_len - len(payload)
            fill_char = "a"
            payload = bytes(payload + n_fill_bytes * fill_char)
            sock_out.sendall(payload)

            print 'sent:', packet_n
            # timeout recv
            try:
                packet = sock_out.recv(packet_len)
            except socket.timeout:
                print 'loss:', packet_n
                continue
            recv_time = time.time()
            payload = packet.rstrip("a")
            (packet_nn, send_time) = pickle.loads(payload)
            latency_us = (recv_time - send_time) * 1e3 / 2
            packets.append((packet_nn, latency_us))
            latency_ms = "%.2f" % latency_us
            out_file.write("%s %s %s\n" % (datetime.datetime.now(), packet_nn, latency_ms))

            tx_end_seconds = time.time()

            # I don't know why, but this still doesn't yield exactly the desired
            # send rate. But eh, it's good enough.
            tx_time_seconds = tx_end_seconds - tx_start_seconds
            sleep_time_seconds = packet_interval - tx_time_seconds
            inter_packet_sleep_times_ms.append("%.3f" % (sleep_time_seconds * 1000))

            # force
            sleep_time_seconds = 1

            if sleep_time_seconds > 0:
                time.sleep(sleep_time_seconds)
        send_end_seconds = time.time()

        print("Finished sending packets!")

        total_send_duration_seconds = send_end_seconds - send_start_seconds
        n_bytes = n_packets * packet_len
        bytes_per_second = n_bytes / total_send_duration_seconds
        print("(Actually sent packets at %d kB/s)" % (bytes_per_second / 1e3))

        # recv
        print("Received %d/%d packets back from server" % (len(packets),
                                                           n_packets))
        #cls.save_packet_latencies(packets, n_packets, output_filename)

        sock_out.close()

    @staticmethod
    def save_packet_latencies(packetn_latency_tuples, n_packets_expected, output_filename):
        """
        Save latencies of received packets to a file, along with the total
        number of packets send in the first place.
        """
        with open(output_filename, 'w') as out_file:
            out_file.write("%d\n" % n_packets_expected)
            for tup in packetn_latency_tuples:
                packet_n = tup[0]
                latency = "%.2f" % tup[1]
                out_file.write("%s %s\n" % (packet_n, latency))
