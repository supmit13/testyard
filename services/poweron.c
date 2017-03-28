#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <arpa/inet.h>
#include <net/if.h>

#include "vix.h"

#define USE_PLAYER
#define VMXPATH_INFO ""
#define BOOT_WAIT_TIME 180 /* Number of seconds the system will wait for the VM to boot */
#ifdef USE_PLAYER

#define  CONNTYPE    VIX_SERVICEPROVIDER_VMWARE_PLAYER

#define  HOSTNAME "192.168.0.101"
#define  HOSTPORT 8333
#define  USERNAME "supriyo"
#define  PASSWORD "spmprx"

#define  VMPOWEROPTIONS   VIX_VMPOWEROP_LAUNCH_GUI   // Launches the VMware Workstaion UI
                                                     // when powering on the virtual machine.

#define VMXPATH_INFO_HELP "where vmxpath is an absolute path to the .vmx file " \
                     "for the virtual machine."

#else    // USE_WORKSTATION

#define CONNTYPE VIX_SERVICEPROVIDER_VMWARE_PLAYER

#define HOSTNAME "https://192.168.0.101:8333/sdk"

/*
 * NOTE: HOSTPORT is ignored, so the port should be specified as part
 * of the URL.
*/
#define HOSTPORT 0
#define USERNAME "supriyo"
#define PASSWORD "spmprx"

#define  VMPOWEROPTIONS VIX_VMPOWEROP_NORMAL

#endif

#define VM_READY_INTERVAL 180 /* This is the time period (in seconds) in which the VM is expected to be up and running */

/*
 * Global variables.
 */

static char *progName;


/*
 * Local functions.
 */

////////////////////////////////////////////////////////////////////////////////

static void usage(){
   fprintf(stderr, "Usage: %s <vmxpath>\n", progName);
   fprintf(stderr, "%s\n", VMXPATH_INFO);
}

////////////////////////////////////////////////////////////////////////////////

int main(int argc, char **argv){
    VixError err;
    char *vmxPath;
    char *ipaddress;
    char *setupIpProg;
    char * readValue;
    VixHandle hostHandle = VIX_INVALID_HANDLE;
    VixHandle jobHandle = VIX_INVALID_HANDLE;
    VixHandle vmHandle = VIX_INVALID_HANDLE;
    VixHandle ipHandle = VIX_INVALID_HANDLE;
    VixHandle waitHandle = VIX_INVALID_HANDLE;
    VixHandle readHandle = VIX_INVALID_HANDLE;
    VixHandle loginHandle = VIX_INVALID_HANDLE;
    VixHandle runHandle = VIX_INVALID_HANDLE;

    progName = argv[0];
    if (argc > 1){
       vmxPath = (char *)malloc(strlen(argv[1]) * sizeof(char));
       strcpy(vmxPath, argv[1]); 
        if(argc > 2){
            ipaddress = (char *)malloc(strlen(argv[2]) * sizeof(char));
            strcpy(ipaddress, argv[2]);
	    setupIpProg = (char *)malloc(strlen("/home/supriyo/scripts/testcode/setIP") * sizeof(char));
	    strcpy(setupIpProg, "/home/supriyo/scripts/testcode/setIP");
        }
    }
    else{
        usage();
        exit(EXIT_FAILURE);
    }
    printf("VM Config PATH: %s\nIP Address: %s\n", vmxPath, ipaddress);
    jobHandle = VixHost_Connect(VIX_API_VERSION, CONNTYPE, HOSTNAME, HOSTPORT, USERNAME, PASSWORD, 
                                0, // options,
                                VIX_INVALID_HANDLE, // propertyListHandle,
                                NULL, // *callbackProc,
                                NULL); // *clientData
    err = VixJob_Wait(jobHandle, VIX_PROPERTY_JOB_RESULT_HANDLE, &hostHandle, VIX_PROPERTY_NONE);
    if (VIX_FAILED(err)){
        goto abort;
    }
    Vix_ReleaseHandle(jobHandle);

    jobHandle = VixVM_Open(hostHandle, vmxPath, NULL, NULL);
    err = VixJob_Wait(jobHandle, VIX_PROPERTY_JOB_RESULT_HANDLE, &vmHandle, VIX_PROPERTY_NONE);
    if (VIX_FAILED(err)){
        goto abort;
    }
    Vix_ReleaseHandle(jobHandle);

    jobHandle = VixVM_PowerOn(vmHandle, VMPOWEROPTIONS, VIX_INVALID_HANDLE, NULL, NULL);
    err = VixJob_Wait(jobHandle, VIX_PROPERTY_NONE);
    if (VIX_FAILED(err)){
        goto abort;
    }
    Vix_ReleaseHandle(jobHandle);

    // sleep(VM_READY_INTERVAL);
    // Wait until guest is completely booted.
    waitHandle = VixVM_WaitForToolsInGuest(vmHandle, BOOT_WAIT_TIME, NULL, NULL); // wait for 180 seconds
    printf("Waiting for the VM to boot\n\n");
    err = VixJob_Wait(waitHandle, VIX_PROPERTY_NONE);
    if (VIX_FAILED(err)){
       // Handle the error...
       goto abort;
    }
    Vix_ReleaseHandle(waitHandle);
    printf("VM booted successfully.\n");
    // Login to the guest machine
    loginHandle = VixVM_LoginInGuest(vmHandle, USERNAME, PASSWORD, 0, NULL, NULL);
    printf("Trying to login into the guest system...\n");
    err = VixJob_Wait(loginHandle, VIX_PROPERTY_NONE);
    if (VIX_FAILED(err)){
        printf("Login to the guest system failed: %s\n\n", Vix_GetErrorText(err, NULL));
        goto abort;
    }
    else{
        printf("Successfully logged in to the guest system...\n");
    }
    Vix_ReleaseHandle(loginHandle);

    printf("Calling setIP with IP address %s - %s\n",ipaddress, setupIpProg);
    runHandle = VixVM_RunProgramInGuest(vmHandle, setupIpProg, ipaddress, 0, VIX_INVALID_HANDLE, NULL, NULL);
    err = VixJob_Wait(runHandle, VIX_PROPERTY_NONE);
    if (VIX_FAILED(err)){
        printf("setIP call failed - %s\n\n",Vix_GetErrorText(err, NULL));
        goto abort;
    }
    Vix_ReleaseHandle(runHandle);
    
    abort:
        Vix_ReleaseHandle(jobHandle);
        Vix_ReleaseHandle(vmHandle);
        Vix_ReleaseHandle(runHandle);
        Vix_ReleaseHandle(loginHandle);
        Vix_ReleaseHandle(waitHandle);
        VixHost_Disconnect(hostHandle);

    return 0;
}

/*
Compile: gcc -I/usr/include/vmware-vix poweron.c -o poweron -lvixAllProducts -ldl -lpthread
Run: ./poweron "/home/supriyo/work/testyard/testyard/vminstances/Linux/UbuntuLinux64_01/UbuntuLinux64_01.vmx"
*/

