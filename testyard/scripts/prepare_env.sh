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
# rsync -v -e ssh prepare_env.sh supriyo@172.16.16.131:/home/supriyo/scripts/ <enter>
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

# Note: You might need to run "sudo dpkg --configure -a" to rectify any dpkg issues.

# -- S.

# Here we go...

rex="^/";

# Do not seek installation/configuration info from user.
export DEBIAN_FRONTEND=noninteractive 

logdir="$(mkdir -p log)"
"$(chmod 777 log)"
logfile="log/prepare_env.log"
echo $logfile, "+++++++++++++++++++++++++++++++++"
echo "Starting environment creation on VM Workstation Player...\n" >> $logfile

locgcc="$(which gcc)";
if [[ $locgcc =~ $rex ]]; then 
    echo "gcc exists"
    echo "* gcc exists\n" >> $logfile 
else 
    instcmd="$(apt-get -y install gcc)"
    echo $instcmd
    echo "$(instcmd >> $logfile)"
fi

locgpp="$(which g++)";
if [[ $locgpp =~ $rex ]]; then 
    echo "g++ exists"
    echo "* g++ exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install g++)"
    echo $instcmd
    echo "$(instcmd >> $logfile)"
fi

locperl="$(which perl)";
if [[ $locperl =~ $rex ]]; then 
    echo "perl exists"
    echo "* perl exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install perl)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locpython="$(which python)";
if [[ $locpython =~ $rex ]]; then 
    echo "python exists"
    echo "* python2.x exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install python)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locpython3="$(which python3)";
if [[ $locpython3 =~ $rex ]]; then 
    echo "python3 exists"
    echo "* python3 exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install python3)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locruby="$(which ruby)";
if [[ $locruby =~ $rex ]]; then 
    echo "ruby exists"
    echo "* ruby exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install ruby)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

loccurl="$(which curl)";
if [[ $loccurl =~ $rex ]]; then 
    echo "curl exists"
    echo "* curl exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install curl)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locmono="$(which mono)";
if [[ $locmono =~ $rex ]]; then 
    echo "mono exists"
    echo "* mono exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install mono)"
    echo $instcmd
    echo $instcmd >> $logfile
fi

locfsharp="$(which fsharp)";
if [[ $locfsharp =~ $rex ]]; then 
    echo "fsharp exists"
    echo "* fsharp exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install mono-complete fsharp)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locgo="$(which go)";
if [[ $locgo =~ $rex ]]; then 
    echo "go exists"
    echo "* go exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install golang)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locjava="$(which java)";
if [[ $locjava =~ $rex ]]; then 
    echo "java exists"
else 
    instcmd="$(apt-get -y install java)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locjs="$(which javascript)";
if [[ $locjs =~ $rex ]]; then 
    echo "javascript exists"
    echo "* javascript exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install javascript)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

loclua="$(which lua)";
if [[ $loclua =~ $rex ]]; then 
    echo "lua exists"
    echo "* lua exists\n" >> $logfile
else 
    instcmd="$(apt-get -y  install lua5.1)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locobjc="$(which clang)";
if [[ $locobjc =~ $rex ]]; then 
    echo "objective-c exists"
    echo "* objective-c -y exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install clang)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locphp="$(which php5)";
if [[ $locphp =~ $rex ]]; then 
    echo "php exists"
    echo "* php exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install php5)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locpascal="$(which fpc)";
fpc
if [[ $locpascal =~ $rex ]]; then 
    echo "Pascal exists"
    echo "* Pascal exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install fpc)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locfortran="$(which gfortran)";
if [[ $locfortran =~ $rex ]]; then 
    echo "fortran exists"
    echo "* fortran exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install gfortran)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

loclisp="$(which lisp)";
if [[ $loclisp =~ $rex ]]; then 
    echo "lisp exists"
    echo "* lisp exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install clisp)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locsmalltalk="$(which gnu-smalltalk)";
if [[ $locsmalltalk =~ $rex ]]; then 
    echo "smalltalk exists"
    echo "* smalltalk exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install gnu-smalltalk)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locscala="$(which scala)";
if [[ $locscala =~ $rex ]]; then 
    echo "scala exists"
    echo "* scala exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install scala)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

loctcl="$(which tclsh)";
if [[ $loctcl =~ $rex ]]; then 
    echo "tclsh exists"
    echo "* tclsh exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install tcl)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locada="$(which ada95 )";
if [[ $locada =~ $rex ]]; then 
    echo "ada95 exists"
    echo "* ada95 exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install gnat-4.4)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locdelphi="$(which lazarus)";
if [[ $locdelphi =~ $rex ]]; then 
    echo "delphi exists"
    echo "* delphi exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install lazarus)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locrust="$(which rust)";
if [[ $locrust =~ $rex ]]; then 
    echo "Rust exists"
    echo "* Rust exists\n" >> $logfile
else 
    instcmd="$(curl -sSf https://static.rust-lang.org/rustup.sh | sh)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locscheme="$(which scheme)";
if [[ $locscheme =~ $rex ]]; then 
    echo "scheme exists"
    echo "* Scheme exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install libmhash2:i386 mit-scheme:i386)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

locswift="$(which swift)";
if [[ $locswift =~ $rex ]]; then 
    echo "swift exists"
    echo "* Swift exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install swift)"
    echo $instcmd
    echo "$instcmd" >> $logfile
fi

loccfm="$(which coldfusion)";
if [[ $loccfm =~ $rex ]]; then 
    echo "coldfusion exists"
    echo "* coldfusion exists\n" >> $logfile
else 
    instcmd="$(apt-get -y install coldfusion)"
    echo $instcmd
    echo "$instcmd" >> $logfile	
fi

# Add openssh server and client on the VM. This will enable another host to
# transfer code to be run on this VM in a secure manner.
instcmd="$(apt-get -y install openssh-server openssh-client)"
echo $instcmd
echo $instcmd >>$logfile

# Now create a directory called 'testcode' in the home directory of the user 
# running this script. The code sent by the execute server (exec_server.c)
# will be copied here and run from this directory. Once they have been run
# and the output/result relayed back, the file(s) will be purged.

curdir="$(pwd)"
testdir="$curdir/testcode"
ipscriptdir="$curdir/scripts"
ipchange_exec_dir="$(mkdir -p $ipscriptdir)"
code_exec_dir="$(mkdir -p $testdir)"

if [ ! -d $testdir ]; then
    echo "Could not create the directory ($testdir) in which the user's code should be run.\n"
    echo "PLEASE CREATE THAT DIRECTORY MANUALLY TO START USING THIS VM WORKSTATION PLAYER.\n"
fi
"$(chmod 777 $testdir)"
if [ ! -d $ipscriptdir ]; then
    echo "Could not create the directory ($ipscriptdir) in which the IP modification code should be run.\n"
    echo "PLEASE CREATE THAT DIRECTORY MANUALLY TO START USING THIS VM WORKSTATION PLAYER.\n"
fi
if [ ! -d $testdir ] || [ ! -d $ipsriptdir ]; then
    echo "Please create the directories above manually. The program failed to create them. This might \
	because of lack of privileges.\n"
else
    # set up the IP manipulation code here... Just get the setIP executable in the '/home/supriyo/testcode' directory.
    "$(rsync -v -e ssh supriyo@192.168.0.101:/home/supriyo/work/testyard/testyard/services/setIP /home/supriyo/scripts/testcode/)"
    # Make root own setIP so that we may set the sticky bit
    "$(sudo chown root:root /home/supriyo/scripts/testcode/setIP)"
    # Now set the sticky bit.
    "$(sudo chmod 4755 /home/supriyo/scripts/testcode/setIP)"
    echo "Thats it! Your machine has been set up to handle all supported languages/technologies. "
    echo "Bye.\n"
fi

# rsync -v -e ssh prepare_env.sh supriyo@172.16.16.132:/home/supriyo/scripts
# Remove earlier ssh keys: ssh-keygen -f "/root/.ssh/known_hosts" -R 172.16.16.136
#--S

