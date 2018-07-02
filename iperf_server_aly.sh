#! /usr/bin/env python

import sys, time

def tail(theFile):
  theFile.seek(0,2)
  while True:
    line = theFile.readline()
    if not line:
      time.sleep(1)
      continue
    yield line

def parse_line(line):
  fields = line.split()
  print len(fields)
  bw = fields[6]
  delay_jitter = fields[8]
  loss_rate = fields[12]
  print bw, delay_jitter, loss_rate

def iperf_server_aly(file_name, client_id):
  with open(file_name, 'r+') as fp:
    for line in tail(fp):
      if line.find('sec') > -1 and \
	 line.find('Mbits/sec') > -1 and \
	 line.find('%d]' % client_id) > -1:
      	parse_line(line)

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print 'Usage: %s file client_id' % sys.argv[0]
    exit(0)
  iperf_server_aly(sys.argv[1], int(sys.argv[2]))
