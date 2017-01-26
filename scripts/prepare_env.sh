#!/bin/bash

# READ BELOW - IMPORTANT
# -----------------------
# This script will attempt to install all the softwares/programming environments
# supported by testyard test code testing feature. The specific environments
# that will be installed are listed in the variable 'COMPILER_LOCATIONS' in the 
# file 'skills_settings.py'. This script should be executed whenever we add another
# new virtual workstation player instance in the VM instances repo at 
# '/home/supriyo/work/testyard/testyard/vminstances/Linux/'. 
# **Note**: This script is supposed to be run on the guest machine, NOT ON THE HOST
# OS. After starting the guest machine, copy this file to a directory in the guest
# machine, provide it with execute permissions (sudo chmod 755 prepare_env.sh), change 
# its ownership to 'root' (sudo chown root:root prepare_env.sh), and run like so:
# sudo  ./prepare_env.sh <enter>
# This should be done from the directory in which you have placed the script. Ideally,
# create a directory named 'scripts' in the home directory (/home/supmit), and place
# it in that directory.

# HOW TO COPY THIS TO THE GUEST MACHINE:
# --------------------------------------
# First, find out the IP address of the guest machine: run ifconfig -a on the guest
# machine from a command prompt on the guest:
# $> ifconfig -a <enter>
# Note the IP address (not the localhost one, that is the one other than 127.0.0.1).
# Let us suppose it is 172.16.16.131 .
# Type the following command from the host machine. This should be executed from the
# directory in which this script resides. For example, if it resides in the directory
# ~/work/testyard/testyard/script, do it in the console from that directory.
# 
# rsync -v -e ssh prepare_env.sh supmit@172.16.16.131:/home/supmit/scripts/ <enter>
#
# We are transferring the file over ssh, so you will be prompted for your password
# of the guest system. Once you type that in, your file should be transferred without
# any glitch. In case you come across any issues at this point, first try to find if
# openssh-server and openssh-client are installed and running on the guest. You may
# do this by running "apt-get install openssh-server openssh-client" on the guest.
# If they are not installed, the above command can install them for you and open 
# port 22 (ssl port), so that the file(s)  will be transferred securely over the 
# network to the guest VMware workstation player. If that doesn't solve your issue,
# please contact your local sysadmin for help. PLEASE ALSO NOTE: my username on the
# guest machine is 'supmit', so my target location is stated as 
# 'supmit@172.16.16.131:/home/supmit/scripts/'. Please change this to the values 
# used by you.

# -- S.

# Here we go...

rex="^/";

locgcc="$(which gcc)";
if [[ $locgcc =~ $rex ]]; then 
    echo "gcc exists"
else 
    instcmd="$(apt-get install gcc)"
    echo $instcmd
fi

locgpp="$(which g++)";
if [[ $locgpp =~ $rex ]]; then 
    echo "g++ exists"
else 
    instcmd="$(apt-get install g++)"
    echo $instcmd
fi

locperl="$(which perl)";
if [[ $locperl =~ $rex ]]; then 
    echo "perl exists"
else 
    instcmd="$(apt-get install perl)"
    echo $instcmd
fi

locpython="$(which python)";
if [[ $locpython =~ $rex ]]; then 
    echo "python exists"
else 
    instcmd="$(apt-get install python)"
    echo $instcmd
fi

locpython3="$(which python3)";
if [[ $locpython3 =~ $rex ]]; then 
    echo "python3 exists"
else 
    instcmd="$(apt-get install python3)"
    echo $instcmd
fi

locruby="$(which ruby)";
if [[ $locruby =~ $rex ]]; then 
    echo "ruby exists"
else 
    instcmd="$(apt-get install ruby)"
    echo $instcmd
fi

loccurl="$(which curl)";
if [[ $loccurl =~ $rex ]]; then 
    echo "curl exists"
else 
    instcmd="$(apt-get install curl)"
    echo $instcmd
fi

locmono="$(which mono)";
if [[ $locmono =~ $rex ]]; then 
    echo "mono exists"
else 
    instcmd="$(apt-get install mono)"
    echo $instcmd
fi

locfsharp="$(which fsharp)";
if [[ $locfsharp =~ $rex ]]; then 
    echo "fsharp exists"
else 
    instcmd="$(apt-get install fsharp)"
    echo $instcmd
fi

locgo="$(which go)";
if [[ $locgo =~ $rex ]]; then 
    echo "go exists"
else 
    instcmd="$(apt-get install go)"
    echo $instcmd
fi

locjava="$(which java)";
if [[ $locjava =~ $rex ]]; then 
    echo "java exists"
else 
    instcmd="$(apt-get install java)"
    echo $instcmd
fi

locjs="$(which javascript)";
if [[ $locjs =~ $rex ]]; then 
    echo "javascript exists"
else 
    instcmd="$(apt-get install javascript)"
    echo $instcmd
fi

loclua="$(which lua)";
if [[ $loclua =~ $rex ]]; then 
    echo "lua exists"
else 
    instcmd="$(apt-get install lua)"
    echo $instcmd
fi

locobjc="$(which clang)";
if [[ $locobjc =~ $rex ]]; then 
    echo "objective-c exists"
else 
    instcmd="$(apt-get install clang)"
    echo $instcmd
fi

locphp="$(which php5)";
if [[ $locphp =~ $rex ]]; then 
    echo "php exists"
else 
    instcmd="$(apt-get install php5)"
    echo $instcmd
fi

locphp="$(which php5)";
if [[ $locphp =~ $rex ]]; then 
    echo "php exists"
else 
    instcmd="$(apt-get install php5)"
    echo $instcmd
fi

locpascal="$(which fpc)";
if [[ $locpascal =~ $rex ]]; then 
    echo "Pascal exists"
else 
    instcmd="$(apt-get install fpc)"
    echo $instcmd
fi

locfortran="$(which gfortran)";
if [[ $locfortran =~ $rex ]]; then 
    echo "fortran exists"
else 
    instcmd="$(apt-get install gfortran)"
    echo $instcmd
fi

loclisp="$(which lisp)";
if [[ $loclisp =~ $rex ]]; then 
    echo "lisp exists"
else 
    instcmd="$(apt-get install lisp)"
    echo $instcmd
fi

locsmalltalk="$(which smalltalk)";
if [[ $locsmalltalk =~ $rex ]]; then 
    echo "smalltalk exists"
else 
    instcmd="$(apt-get install smalltalk)"
    echo $instcmd
fi

locscala="$(which scala)";
if [[ $locscala =~ $rex ]]; then 
    echo "scala exists"
else 
    instcmd="$(apt-get install scala)"
    echo $instcmd
fi

loctcl="$(which tclsh)";
if [[ $loctcl =~ $rex ]]; then 
    echo "tclsh exists"
else 
    instcmd="$(apt-get install tclsh)"
    echo $instcmd
fi

locada="$(which ada95)";
if [[ $locada =~ $rex ]]; then 
    echo "ada95 exists"
else 
    instcmd="$(apt-get install ada95)"
    echo $instcmd
fi

locdelphi="$(which delphi)";
if [[ $locdelphi =~ $rex ]]; then 
    echo "delphi exists"
else 
    instcmd="$(apt-get install delphi)"
    echo $instcmd
fi

locrust="$(which rust)";
if [[ $locrust =~ $rex ]]; then 
    echo "Rust exists"
else 
    instcmd="$(apt-get install rust)"
    echo $instcmd
fi

locscheme="$(which scheme)";
if [[ $locscheme =~ $rex ]]; then 
    echo "scheme exists"
else 
    instcmd="$(apt-get install scheme)"
    echo $instcmd
fi

locswift="$(which swift)";
if [[ $locswift =~ $rex ]]; then 
    echo "swift exists"
else 
    instcmd="$(apt-get install swift)"
    echo $instcmd
fi

loccfm="$(which coldfusion)";
if [[ $loccfm =~ $rex ]]; then 
    echo "coldfusion exists"
else 
    instcmd="$(apt-get install coldfusion)"
    echo $instcmd
fi

echo "Thats it! Your machine has been set up to handle all supported languages/technologies. "
echo "Bye.\n"



