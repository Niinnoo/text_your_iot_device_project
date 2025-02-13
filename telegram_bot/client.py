from aiocoap import *
import os

PSK_IDENTITY = os.environ.get("PSK_IDENTITY").encode('utf-8')
PSK_KEY      = os.environ.get("PSK_KEY").encode('utf-8')

# Function to send a GET request to the specified resource
async def coap_client(resource):
    IP_ADDRESS = os.environ.get("COAP_SERVER_IP")

    if not IP_ADDRESS:
        raise ValueError("Client: Environment variable COAP_SERVER_IP is not set")

    # Target address for the RIOT device (CoAP server) and resource
    coap_server_uri = f"coaps://[{IP_ADDRESS}]/{resource}"
    
    # Create a CoAP GET request
    request = Message(code=GET, uri=coap_server_uri)

    try:
        # Initialize the CoAP protocol
        protocol = await Context.create_client_context()
        print(f"Send request to {coap_server_uri} ...")
        
        # Add PSK Credentials to the server for DTLS Communication
        protocol.client_credentials.load_from_dict({
            coap_server_uri : {
                'dtls' : {
                    'psk' : PSK_KEY,
                    'client-identity' : PSK_IDENTITY
                }
            }
        })

        # Send the request and wait for the response
        response = await protocol.request(request).response

        decoded_response = response.payload.decode('utf-8')
        print(f"Client: Response from server: {decoded_response}")
        return decoded_response

    except UnboundLocalError as e:
        print("Client: Connection established, but the sensor data could not be retrieved from the IoT device.")
        raise e

    except Exception as e:
        print(f"Client: Error accessing the CoAP server: {e}")
        raise e

    finally:
        await protocol.shutdown()
