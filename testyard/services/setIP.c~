#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/ioctl.h>
#include <arpa/inet.h>
#include <net/if.h>



/* Set IP Address of this VM */
int main(int argc, char *argv[]){
    char *ipaddress;
    struct ifreq ifr;
    const char * name = "eth0";
    struct sockaddr_in* addr;
    int fd = socket(PF_INET, SOCK_DGRAM, IPPROTO_IP);
    if(argc > 1){
        ipaddress = (char *)malloc(strlen(argv[1]) * sizeof(char));
        strcpy(ipaddress, argv[1]);
    }
    /* printf("Entered setIP...\n\n"); */
    strncpy(ifr.ifr_name, name, IFNAMSIZ);
    ifr.ifr_addr.sa_family = AF_INET;
    addr = (struct sockaddr_in*)&ifr.ifr_addr;
    inet_pton(AF_INET, ipaddress, &addr->sin_addr);
    ioctl(fd, SIOCSIFADDR, &ifr);
                                                                                                                                                                                                                                                                                                                                           
    inet_pton(AF_INET, "255.255.255.0", ifr.ifr_addr.sa_data + 2);
    ioctl(fd, SIOCSIFNETMASK, &ifr);

    ioctl(fd, SIOCGIFFLAGS, &ifr);
    strncpy(ifr.ifr_name, name, IFNAMSIZ);
    ifr.ifr_flags |= (IFF_UP | IFF_RUNNING);

    ioctl(fd, SIOCSIFFLAGS, &ifr);
    /* printf("Set IP address complete - %s\n", ipaddress); */
    return 0;
}
/*
Compile: gcc -I/usr/include/vmware-vix -o setIP setIP.c -lvixAllProducts -ldl
Run: Should be called from within poweron.c
*/

