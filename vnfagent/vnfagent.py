import threading
import json
import asyncore,socket
import datetime
import sys
from argparse import ArgumentParser
from utils import *
import logging
import docker
import os
import signal
from vnf import VNF
CTRL_IP='192.168.109.144'
CTRL_PORT = 6699
SWITCH_DPID=1
SWITCH_LISTEN=6634

def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('ascii')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv
def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('ascii')
        if isinstance(value, unicode):
            value = value.encode('ascii')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv

class VNFClient(asyncore.dispatcher):
    def __init__(self,ctrl_ip,ctrl_port,dpid,listen):
        asyncore.dispatcher.__init__(self)
        self.ctrl_ip=ctrl_ip
        self.ctrl_port=ctrl_port
        self.switch_dpid=dpid
        self.docker=docker.from_env()
        self.switch_listen_port=listen
        self.vnfs={}
        self.write_buffer = ''
        self.recv_buffer = ''
        self.init_connection()

    def init_connection(self):
        try:
            self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error:
            pass
        try:
            self.connect((self.ctrl_ip,self.ctrl_port))
            logging.info("Connecting to controller")
        except socket.error:
            pass

    def send_msg(self,msg):
        self.write_buffer += json.dumps(msg)+'\n'

    def handle_connect(self):
        obj = {
            'type':'HELLO',
            'dpid':self.switch_dpid
        }
        self.send_msg(obj)

    def writable(self):
        if not self.connected:
            return True
        return (len(self.write_buffer)>0)

    def handle_write(self):
        sent = self.send(self.write_buffer)
        print 'send bytes', sent
        self.write_buffer = self.write_buffer[sent:]

    def handle_error(self):
        print 'Handling connection error, reconnecting ...'
        self.init_connection()

    def handle_close(self):
        print 'Handling connection disconnect, reconnecting ...'
        self.close()
        self.init_connection()

    def handle_read(self):
        msg_buffer =self.recv(1024)
        print msg_buffer
        if msg_buffer:
            msg=json.loads(msg_buffer,object_hook=_decode_dict)
            handler_name ="_handle_%s" %msg['type']
            if not hasattr(self,handler_name):
                print "Unknown message type:",msg['type']
                return
            handler=getattr(self,handler_name)
            handler(msg)

    def _handle_add_vnf(self,msg):
        vnf_id=int(msg['vnf_id'])
        tenant_id=int(msg['tenant_id'])
        nb_ports=int(msg['nb_ports'])
        type =msg['vnf_type']
        script=msg['script']
       # vnf = VNF(self,tenant_id,vnf_id,type,nb_ports, script)
       # vnf.start()
       # self.vnfs[tenant_id]=vnf

    def _handle_del_vnf(self,msg):
        vnf_id=int(msg['vnf_id'])
        if vnf_id not in self.vnfs:
             raise KeyError("LVNF %s not found" % vnf_id)
        vnf = self.vnfs[vnf_id]
        vnf.stop()
        del self.vnfs[vnf_id]

class Watcher():

    def __init__(self):
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            self.kill()
        sys.exit()

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError:
            pass

def main():
    """Parse the command line and set the callbacks"""
    usage = "%s [options]" % sys.argv[0]
    parser = ArgumentParser(usage=usage)
    parser.add_argument("-c","--ctrl",dest="ctrl",default=CTRL_IP,help="Controller address;default=%s" % CTRL_IP)
    parser.add_argument("-p","--port",dest="port",default=CTRL_PORT,type=int,help="Controller port;default=%u" % CTRL_PORT)
    parser.add_argument("-d","--dpid",dest="dpid",default=SWITCH_DPID,type=int,help="Switch dpid;default=%u" % SWITCH_DPID)
    parser.add_argument("-l","--listen",dest="listen",default=SWITCH_LISTEN,type=int,help="Switch listen port;default=%u" % SWITCH_LISTEN)
    (args, _) = parser.parse_known_args(sys.argv[1:])
    Watcher()
    vnfagent=VNFClient(args.ctrl,args.port,args.dpid,args.listen)
    asyncore.loop(timeout=1)

if __name__=="__main__":
    main()
