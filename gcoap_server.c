/** 
* @{ 
* Implements the functionality of the CoAP server, parts of this program are from the 
* GCoAP example of RIOT.
* Source: https://github.com/RIOT-OS/RIOT/tree/master/examples/gcoap_dtls
*
* @authors Clemens Friesl <clemens.friesl@stud.fra-uas>; 
           Nino Zoric     <nino.zoric@stud.fra-uas,de>; 
           Paul Lakus     <paul.lakus@stud.fra-uas.de>
* @}
*/

#include "tinydtls_keys.h"
#include "gcoap_server.h"
#include "saul.h"

/*
    DTLS credentials data defined here.
*/
#if IS_USED(MODULE_GCOAP_DTLS)
#include "net/credman.h"
#include "net/dsm.h"
#include "sock_dtls_types.h"

/* Credentials for DTLS PSK-ID and KEY. */
#define SOCK_DTLS_SERVER_TAG (10)

static const uint8_t psk_id_0[] = PSK_DEFAULT_IDENTITY;
static const uint8_t psk_key_0[] = PSK_DEFAULT_KEY;
static const credman_credential_t credential = {
    .type = CREDMAN_TYPE_PSK,
    .tag = SOCK_DTLS_SERVER_TAG,
    .params = {
        .psk = {
            .key = {
                .s = psk_key_0,
                .len = sizeof(psk_key_0) - 1,
            },
            .id = {
                .s = psk_id_0,
                .len = sizeof(psk_id_0) - 1,
            },
        }},
};
#endif

/* CoAP resources */
static const coap_resource_t _resources[] = {
    {"/internal_temp", COAP_GET, _internal_temp_handler, NULL},
    {"/external_temp", COAP_GET, _external_temp_handler, NULL},
    {"/hum", COAP_GET, _external_humid_handler, NULL},
};


static gcoap_listener_t _listener = {
    &_resources[0],
    ARRAY_SIZE(_resources),
    GCOAP_SOCKET_TYPE_UNDEF,
    NULL,
    NULL,
    NULL
};


/*
   Handler function for GET /internal_temp -> returns the internal temperature of the board.
*/
static ssize_t _internal_temp_handler(coap_pkt_t *pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx)
{
    (void)ctx;
    gcoap_resp_init(pdu, buf, len, COAP_CODE_CONTENT);
    coap_opt_add_format(pdu, COAP_FORMAT_TEXT);
    size_t resp_len = coap_opt_finish(pdu, COAP_OPT_FINISH_PAYLOAD);

    /* Read internal temperature sensor */
    char buffer[INTERNAL_TEMP_SENSOR_BUF_SIZE];
    if (get_temp_sensor_formatted(buffer, INTERNAL_TEMP_SENSOR_BUF_SIZE) != 0)
    {
        return gcoap_response(pdu, buf, len, COAP_CODE_SERVICE_UNAVAILABLE);
    }
    else
    {
        printf("Interne Temperatursensor Anfrage ergibt: %s\n", buffer);
        memcpy((char *)pdu->payload, buffer, INTERNAL_TEMP_SENSOR_BUF_SIZE);
        resp_len += sizeof(pdu->payload);
        return resp_len;
    }
}

/*
    Handler function for GET /external_temp -> returns the DHT11 temperature.
*/
static ssize_t _external_temp_handler(coap_pkt_t *pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx)
{
    (void)ctx;
    gcoap_resp_init(pdu, buf, len, COAP_CODE_CONTENT);
    coap_opt_add_format(pdu, COAP_FORMAT_TEXT);
    size_t resp_len = coap_opt_finish(pdu, COAP_OPT_FINISH_PAYLOAD);
    
    /* Read external temperature sensor */
    char buffer[EXTERNAL_TEMP_SENSOR_BUF_SIZE];
    if(get_dht_temp(buffer) != 0){
        return gcoap_response(pdu, buf, len, COAP_CODE_SERVICE_UNAVAILABLE);
    }
    else
    {
        printf("DHT Temperatursensor Anfrage ergibt: %s\n", buffer);
        memcpy((char *)pdu->payload, buffer, EXTERNAL_TEMP_SENSOR_BUF_SIZE);
        resp_len += sizeof(pdu->payload);
        return resp_len;
    }
}

/*
    Handler function for GET /hum -> returns the DHT11 humidity.
*/
static ssize_t _external_humid_handler(coap_pkt_t *pdu, uint8_t *buf, size_t len, coap_request_ctx_t *ctx)
{
    (void)ctx;
    gcoap_resp_init(pdu, buf, len, COAP_CODE_CONTENT);
    coap_opt_add_format(pdu, COAP_FORMAT_TEXT);
    size_t resp_len = coap_opt_finish(pdu, COAP_OPT_FINISH_PAYLOAD);

    /* Read external humidity sensor */
    char buffer[EXTERNAL_HUM_SENSOR_BUF_SIZE];
    if(get_dht_hum(buffer) != 0){
        return gcoap_response(pdu, buf, len, COAP_CODE_SERVICE_UNAVAILABLE);
    }
    else
    {
        printf("DHT Humidity-Sensor Anfrage ergibt: %s\n", buffer);
        memcpy((char *)pdu->payload, buffer, EXTERNAL_TEMP_SENSOR_BUF_SIZE);
        resp_len += sizeof(pdu->payload);
        return resp_len;
    }
}

/* 
     Server initialization, called exactly once at startup
*/
void server_init(void)
{
#if IS_USED(MODULE_GCOAP_DTLS)
    int res = credman_add(&credential);
    if (res < 0 && res != CREDMAN_EXIST)
    {
        /* ignore duplicate credentials */
        printf("GCoAP: cannot add credentials to the system, response: %d\n", res);
        return;
    }
    sock_dtls_t *gcoap_sock_dtls = gcoap_get_sock_dtls();
    res = sock_dtls_add_credential(gcoap_sock_dtls, SOCK_DTLS_SERVER_TAG);
    if (res < 0)
    {
        printf("GCoAP: cannot add credential to DTLS socket, response: %d\n", res);
    }
#endif

    gcoap_register_listener(&_listener);
}
