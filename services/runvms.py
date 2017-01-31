#!/usr/bin/python

import os, sys, re, time
import subprocess


if __name__ == "__main__":
    vmscount = 2
    runcmd = "/home/supriyo/work/testyard/testyard/services/poweron" 
    runsetIp = "/home/supriyo/work/testyard/testyard/services/setIP"
    runcmdargbeg = "/home/supriyo/work/testyard/testyard/vminstances/Linux/"
    ipAddresseslist = ['192.168.0.102', '192.168.0.103', '192.168.0.104', '192.168.0.105', '192.168.0.106', '192.168.0.107', '192.168.0.108', '192.168.0.109', '192.168.0.110', '192.168.0.111' ]
    # Iterate through the VM instances for starting them one by one.
    for i in range(1, vmscount):
        istr = str(i)
        if len(istr) < 2:
            istr = '0' + istr
        instancestr = "UbuntuLinux%s/UbuntuLinux%s.vmx"%(istr, istr)
	# TO DO: We need to change/set the IP address of the VM here by manipulating the VMX (config) file.
        runcmdarg = runcmdargbeg + instancestr
        print runcmdarg
        runvmsout = subprocess.Popen([runcmd, runcmdarg, ipAddresseslist[i-1], runsetIp], stdin=None, stdout=None, stderr=None, close_fds=True).communicate()[0];
        print "Output from the power on command on VM with IP address %s -- \n"%ipAddresseslist[i-1], runvmsout

#vminstance01/vminstance01.vmx
