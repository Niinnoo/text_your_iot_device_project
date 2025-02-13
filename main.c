/** 
* @{ 
* Mainfile, starts the CoAP server and the shell with two new commands.
*
* @authors Clemens Friesl <clemens.friesl@stud.fra-uas>; 
           Nino Zoric     <nino.zoric@stud.fra-uas,de>; 
           Paul Lakus     <paul.lakus@stud.fra-uas.de>
* @}
*/

#include <stdio.h>
#include "msg.h"

#include "net/gcoap.h"
#include "shell.h"
#include "xtimer.h"

#include "gcoap_server.h"
#include "saul.h"

#define MAIN_QUEUE_SIZE (4)
static msg_t _main_msg_queue[MAIN_QUEUE_SIZE];

static const shell_command_t shell_commands[] = {
    { "saul_test", "SAUL Testing", saul_test },
    { "dht", "DHT Testing", print_dht_sensor_val },
    { NULL, NULL, NULL }
};

int main(void){
    msg_init_queue(_main_msg_queue, MAIN_QUEUE_SIZE);
    server_init();

    char line_buf[SHELL_DEFAULT_BUFSIZE];
    shell_run(shell_commands, line_buf, SHELL_DEFAULT_BUFSIZE);
    return 0;
}
