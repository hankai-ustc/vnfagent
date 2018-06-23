import subprocess


def exec_cmd(cmd):
    output = subprocess.check_output(cmd,stderr=subprocess.STDOUT).strip()
    return output



def get_ports():
    cmd = ["pofsctrl","-d","ports"]
    ports = {}
    lines =exec_cmd(cmd).split('\n')
    for line in lines:
        result = line.strip().split(' ')[0:3]
        port_name = result[1].strip().split('=')[1]
        port_id = result[2].strip().split('=')[1]
        ports[port_name]=port_id
    return ports

def get_port(ifname):
    cmd = ["pofsctrl","-d","ports"]
    ports = {}
    lines =exec_cmd(cmd).split('\n')
    port = None
    for line in lines:
        result = line.strip().split(' ')[0:3]
        port_name = result[1].strip().split('=')[1]
        port_id = result[2].strip().split('=')[1]
        if port_name == ifname:
            port=port_id
            break
    return port

def add_switch_port(ifname):
    subcmd="addport:%s" %ifname
    cmd = ["pofsctrl","-d",subcmd]
    exec_cmd(cmd)
    port_id=get_port(ifname)
    return port_id


def del_switch_port(ifname):
    subcmd="delport:%s" %ifname
    cmd = ["pofsctrl","-d",subcmd]


def get_cpu_stats(self):
    with open('/proc/stat', 'r') as f:
        line = f.readline()
        user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice = map(int, line.split()[1:])
        usertime = user - guest
        nicetime = nice - guest_nice
        idlealltime = idle + iowait
        systemalltime = system + irq + softirq
        virtalltime = guest + guest_nice
        totaltime = usertime + nicetime + systemalltime + idlealltime + steal + virtalltime

        return {
            'idle': idlealltime,
            'total': totaltime
        }
def get_mem_stats(self):
    stats = {}
    units = {
        'kB': 1024,
        'MB': 1024**2
    }

    with open('/proc/meminfo', 'r') as f:
       for line in f:
           key, value, unit = line.split()
           stats[key[:-1]] = int(value) * units[unit]

    return {
        'free': stats['MemFree'],
        'total': stats['MemTotal']
    }

def create_veth_pair(iface1,iface2):
    cmd = ["ip","link","add",iface1,"type","veth","peer","name",iface2]
    exec_cmd(cmd)

def get_docker_nspid(container_name):
    cmd = ["docker","inspect","-f","'{{.State.Pid}}'","container_name"]
    nspid = exec_cmd(cmd).strip()
    return nspid

def add_iface_to_container(container_name,iface1,iface2):
    nspid = get_docker_nspid(container_name)
    subcmd1="/proc/%s/ns/net" %nspid
    subcmd2="/var/run/netns/%s" %nspid
    exec_cmd(["ln","-s",subcmd1,subcmd2])
    exec_cmd(["ip","link","set","dev",iface1,"name",iface2,"netns",nspid])
    exec_cmd(["ip","netns","exec",nspid,"ip","link","set","dev",iface2,"up"])
