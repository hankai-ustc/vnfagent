import subprocess

def exec_cmd(cmd,timeout=2):
    """Execute command and return its output.

    Raise:
        IOError, if the timeout expired or if the command returned and error
    """

    output = subprocess.check_output(cmd,stderr=subprocess.STDOUT).strip()
    return output
	
def get_ports():
    cmd = ["pofsctrl","-d","ports"]
    i=0
    lines = exec_cmd(cmd).split('\n')
    for line in lines:
	    result = line.split('  ')[1]
        port_name = result.strip().split('=')[1]
        print port_name
	
if __name__ == '__main__':
    get_ports()
    
