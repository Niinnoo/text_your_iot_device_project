/** 
* @{ 
* Header file for CoAP Server.
*
* @authors Clemens Friesl <clemens.friesl@stud.fra-uas>; 
           Nino Zoric     <nino.zoric@stud.fra-uas,de>; 
           Paul Lakus     <paul.lakus@stud.fra-uas.de>
* @}
*/

#include <stdio.h>
#include <string.h>
#include "net/gcoap.h"

/* 
    Server initialization, is called exactly once at startup.
*/
void server_init(void);

/*
    Handler function for GET /internal_temp -> returns the internal temperature of the board.
*/
static ssize_t _internal_temp_handler(coap_pkt_t *pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx);


/*
    Handler function for GET /external_temp -> returns the DHT11 temperature.
*/
static ssize_t _external_temp_handler(coap_pkt_t *pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx);

/*
    Handler function for GET /hum -> returns the DHT11 humidity.
*/
static ssize_t _external_humid_handler(coap_pkt_t *pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx);
