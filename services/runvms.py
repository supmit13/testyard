import os, sys, re, time
import subprocess


if __name__ == "__main__":
    vmscount = 2
    runcmd = "/home/supriyo/work/testyard/testyard/services/poweron" 
    runcmdargbeg = "/home/supriyo/work/testyard/testyard/vminstances/Linux/"
    # Iterate through the VM instances for starting them one by one.
    for i in range(1, vmscount):
        istr = str(i)
        if len(istr) < 2:
            istr = '0' + istr
        instancestr = "UbuntuLinux%s/UbuntuLinux%s.vmx"%(istr, istr)
        runcmdarg = runcmdargbeg + instancestr
        print runcmdarg
        runvmsout = subprocess.Popen([runcmd, runcmdarg], stdin=None, stdout=None, stderr=None, close_fds=True).communicate()[0]
        print str(runvmsout)

#vminstance01/vminstance01.vmx
# Run as: python runvms.py
# This will start up as many virtual machines as specified by vmscount variable.
