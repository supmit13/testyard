#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "vix.h"

#define USE_PLAYER
#define VMXPATH_INFO ""
#ifdef USE_PLAYER

#define  CONNTYPE    VIX_SERVICEPROVIDER_VMWARE_PLAYER

#define  HOSTNAME "192.168.0.101"
#define  HOSTPORT 8333
#define  USERNAME "supmit"
#define  PASSWORD "spmprx"

#define  VMPOWEROPTIONS   VIX_VMPOWEROP_LAUNCH_GUI   // Launches the VMware Workstaion UI
                                                     // when powering on the virtual machine.

#define VMXPATH_INFO_HELP "where vmxpath is an absolute path to the .vmx file " \
                     "for the virtual machine."

#else    // USE_WORKSTATION

/*
 * For VMware Server 2.0
 */

#define CONNTYPE VIX_SERVICEPROVIDER_VMWARE_PLAYER

#define HOSTNAME "https://192.168.0.101:8333/sdk"

/*
 * NOTE: HOSTPORT is ignored, so the port should be specified as part
 * of the URL.
*/
#define HOSTPORT 0
#define USERNAME "supmit"
#define PASSWORD "spmprx"

#define  VMPOWEROPTIONS VIX_VMPOWEROP_NORMAL

#endif    // USE_WORKSTATION

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
    VixHandle hostHandle = VIX_INVALID_HANDLE;
    VixHandle jobHandle = VIX_INVALID_HANDLE;
    VixHandle vmHandle = VIX_INVALID_HANDLE;

    progName = argv[0];
    if (argc > 1){
       vmxPath = (char *)malloc(strlen(argv[1]) * sizeof(char));
       strcpy(vmxPath, argv[1]); 
    } 
    else{
        usage();
        exit(EXIT_FAILURE);
    }

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
    /*
    jobHandle = VixVM_PowerOff(vmHandle, VIX_VMPOWEROP_NORMAL, NULL, NULL);
    err = VixJob_Wait(jobHandle, VIX_PROPERTY_NONE);
    if (VIX_FAILED(err)){
        goto abort;
    }
    */

abort:
    Vix_ReleaseHandle(jobHandle);
    Vix_ReleaseHandle(vmHandle);
    VixHost_Disconnect(hostHandle);

    return 0;
}

/*
Compile: gcc -I/usr/include/vmware-vix poweron.c -o poweron -lvixAllProducts -ldl -lpthread
Run: ./poweron "/home/supriyo/work/testyard/testyard/vminstances/Linux/UbuntuLinux01/UbuntuLinux01.vmx"
*/

