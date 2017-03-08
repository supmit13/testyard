# Process of getting a VM up and running:
# 1. Create the VM instance using the workstation player bundle and the OS iso file.
# 2. Navigate to the "services" directory from the command line. Open up this file (runvms.py) and set the value of 'vmscount' appropriately.
# 3. Fire this script from the command lime like so: $> python runvms.py. This will run the "poweron"  program and get your VM(s) running.
# 4. Login into the VM  using the appropriate user id ('supmit' in my case here), and go to the scripts dir. 
# 5. Using 'rsync', copy the file prepare_env.sh from the system on which it is located. For this operation, please refer to the help
# mentioned in the file 'prepare_env.sh'.
# 6. The above script will prepare the software env on the newly created VM as well as set up the IP address appropriately.
# 7. That concludes the process of getting a VM up and running.
# --S


import os, sys, re, time
import subprocess
sys.path.insert(0, "/home/supriyo/work/testyard/testyard/skillstest")
from skillstest import settings as mysettings


if __name__ == "__main__":
    vmscount = mysettings.MAX_VM_INSTANCES_LIN
    runcmd = "/home/supriyo/work/testyard/testyard/services/poweron" 
    #runsetIp = "/home/supriyo/work/testyard/testyard/services/setIP"
    runsetIp = "/home/supriyo/scripts/testcode/setIP" # Path to the setIP in the player.
    runcmdargbeg = "/home/supriyo/work/testyard/testyard/vminstances/Linux/"
    ipAddresseslist = [ '192.168.0.102', '192.168.0.103', '192.168.0.104', '192.168.0.105', '192.168.0.106', '192.168.0.107', '192.168.0.108', '192.168.0.109', '192.168.0.110', '192.168.0.111' ]
    # Iterate through the VM instances for starting them one by one.
    for i in range(6, vmscount):
        istr = str(i)
        if len(istr) < 2:
            istr = '0' + istr
        instancestr = "UbuntuLinux64_%s/UbuntuLinux64_%s.vmx"%(istr, istr)
	# TO DO: We need to change/set the IP address of the VM here by manipulating the VMX (config) file.
        runcmdarg = runcmdargbeg + instancestr
        print runcmdarg
        runvmsout = subprocess.Popen([runcmd, runcmdarg, ipAddresseslist[i-1], runsetIp], stdin=None, stdout=None, stderr=None, close_fds=True).communicate()[0];
        print "Output from the power on command on VM with IP address %s --\n"%ipAddresseslist[i-1], runvmsout

#vminstance01/vminstance01.vmx
