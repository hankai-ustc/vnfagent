import sys
from utils import *
import os
import docker
class VNF():
    def __init__(self,agent,tenant_id,vnf_id,type,nb_ports,script):
        self.agent =agent
        self.nb_ports=nb_ports
        self.tenant_id=tenant_id
        self.vnfid = vnf_id
        self.script = script
        self.container_name="vnf-%s" %self.vnfid
        self.script_path="/home/hankai/vnf-scripts/"
        self.script_name='vnf-%u-start'%self.vnfid
        self.create_shell_cmd()
        self.ports={}

    def create_shell_cmd(self):
        os.chdir(self.script_path)
        if os.path.exists(self.script_name):
            print "ERROR:'%s' already exists" %self.script_name
            return False
        fobj=open(self.script_name,'w')
        line1="#!/bin/bash\n"
        fobj.writelines([line1,self.script])
        fobj.close()
        file="%s%s" %(self.script_path,self.script_name)
        exec_cmd(["chmod","u+x",file])

    def del_shell_cmd(self):
        os.chdir(self.script_path)
        if os.path.exists(self.script_name):
            os.remove(self.script_name)

    def container_cmd(self,cmd):
        exec_cmd(cmd)

    def start(self):
        self.create_ports()
        subcmd="%s%s:/usr/local/bin/start" %(self.script_path,self.script_name)
        cmd = ["docker","run","-itd","--rm","--name",self.container_name,"--privileged","-v",subcmd,"base"]
        self.container_cmd(cmd)
        for i in range(self.nb_ports):
            ifname0="vnf-%s-%s-outside" %(self.vnfid,i)
            ifname1="vnf-%s-%s-inside" %(self.vnfid,i)
            ifname2="eth%s" %i
            add_iface_to_container(self.container_name,ifname1,ifname2)
            switch_port_id=add_switch_port(ifname0)
            self.port[i]=[switch_port_id,ifname0,ifname2]

    def stop(self):
        self.del_shell_cmd()
        cmd = ["docker","stop",self.container_name]
        self.container_cmd(cmd)

    def create_ports(self):
        for i in range(self.nb_ports):
            iface1 = "vnf-%u-%u-inside" %(self.vnfid,i)
            iface2 = "vnf-%u-%u-outside" %(self.vnfid,i)
            create_veth_pair(iface1,iface2)


