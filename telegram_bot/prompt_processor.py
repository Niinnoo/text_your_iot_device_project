import json
from ollama import AsyncClient
import subprocess
import asyncio
from client import coap_client
from settings_handler import Settings

class Prompt_Processor:
    def __init__(self, model="llama3.2:1b-instruct-q4_0", num_predict=None, format="json"):
        self.model = model
        self.stream = False
        if num_predict:
            self.options = {
                "num_predict": num_predict
            }
        else:
            self.options = {}
        self.format = format
        self.system_description = (
            'You are a helpful assistant that processes user requests and responds strictly in JSON format. Analyze the input and select the MOST SPECIFIC action from the allowed list below: '
            # Allowed Actions: 
            '1. **unknown**: Use if the request is unclear, ambiguous, or unrelated to defined actions. '
            '2. **help**: Use if the user asks for help, instructions, or support. '
            '3. **humidity**: Use if the request explicitly or contextually refers to **humidity** (e.g., wet, dry, moisture). '
            '4. **get_internal_temp**: Use if the request explicitly or contextually refers to **indoor temperature** (e.g., inside a room, building, or device). '
            '5. **get_external_temp**: Use if the request explicitly or contextually refers to **outdoor temperature** (e.g., outside, weather, environment). '
            '6, **temperature**: Use if the request explicitly or contextually refers to **temperature** (e.g., hot, cold, warm). '
            # Response Format: 
            'Always respond in JSON format with the chosen action and empty parameters: '
            '```json '
            '{"action": "action_name"} '
        )

        self.function_registry = {
            "get_temperature": self.get_temperature,
            "temperature": self.get_temperature,
            "resource": self.get_resource,
            "unknown": self.unknown,
            "help": self.help,
            "unavailable": self.unavailable,
            "get_internal_temp": self.get_internal_temp,
            "get_external_temp": self.get_external_temp,
            "humidity": self.get_humidity,
            "get_humidity": self.get_humidity
        }
        self.settings = Settings()

    async def get_internal_temp(self, user_id, **kwargs):
        return await self.get_sensor_value(user_id, resource="internal_temp")

    async def get_external_temp(self, user_id, **kwargs):
        return await self.get_sensor_value(user_id, resource="external_temp")

    async def get_temperature(self, user_id, **kwargs):
        return "choose_temperature_sensor"

    async def get_humidity(self, user_id, **kwargs):
        return await self.get_sensor_value(user_id, resource="hum")

    def convert_temperature_unit(self, temperature, unit):
        # Temperature is already in Celsius
        if unit.lower() == "c":
            return temperature
        # Convert temperature from Celsius to Fahrenheit
        elif unit.lower() == "f":
            return (temperature * 9/5) + 32

    async def get_sensor_value(self, user_id, resource, **kwargs):
        """Calls the method coap_client async."""
        try:
            response = await coap_client(resource) # external_temp or internal_temp
            if response is not None:
                try:
                    if resource == 'hum':
                        temp_unit = "%"
                        temperature = response
                    else:
                        temp_unit = self.settings.get_user_temp_unit(str(user_id))
                        temperature = self.convert_temperature_unit(float(response),temp_unit)
                        temp_unit = '°' + temp_unit
                except ValueError as e:
                    print(f"Prompt processor: Sensor value is not a number: {response}")
                    raise e
                response = f"{temperature} {temp_unit.upper()}"
                return response
            else:
                print("Prompt processor: Connection established, but no data received.")
                return None
            
        except ValueError as e:
            print("Prompt processor: Environment variable COAP_SERVER_IP is not set")
            raise e
        
        except Exception as e:
            print(f"Prompt processor: get_sensor_value returned exception: {e}")
            if "No suitable credentials" in str(e):
                return self.settings.get_translation(self.settings.get_user_language(str(user_id)),"coap_credentials_error")
            else:
                raise e

        
    async def get_resource(self, user_id, **kwargs):
        try:
            result = subprocess.run(['python3', 'client.py'], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return self.settings.get_translation(self.settings.get_user_language(str(user_id)),"unknown_command",error=e)


    def unknown(self, user_id, **kwargs):
        return self.settings.get_translation(self.settings.get_user_language(str(user_id)),"unknown_command")

    def help(self, user_id, **kwargs):
        return self.settings.get_translation(self.settings.get_user_language(str(user_id)),"help")

    def unavailable(self, user_id, **kwargs):
        return self.settings.get_translation(self.settings.get_user_language(str(user_id)),"llm_unavailable")

    async def process(self, prompt):
        print("Received prompt: " + prompt)
        if prompt.lower() in self.function_registry:
            return prompt.lower()
        response = await AsyncClient().generate(model=self.model, prompt=prompt, stream=self.stream, system=self.system_description, options=self.options, format=self.format)
        return response['response']

    def parse_json(self, str) -> str:
        try:
            data = json.loads(str)
            return data
        except (json.JSONDecodeError, TypeError):
            data = json.loads('{"action": "unknown", "parameters": {}}')
            return data

    async def process_action(self, response, user_id):
        print("Received response: " + response)
        parameters = {}
        if response in self.function_registry:
            action = response
        else:
            action_data = self.parse_json(response)
            try:
                action = action_data.get("action", "unknown")
                parameters = action_data.get("parameters", {})
            except Exception:
                action = "unknown"

        print("Executed action: " + action)
        if action in self.function_registry:
            try:
                if asyncio.iscoroutinefunction(self.function_registry[action]):
                    result = await self.function_registry[action](user_id, **parameters)                
                else:
                    result = self.function_registry[action](user_id, **parameters)
                return result
            except TypeError as e:
                return self.unknown()
        else:
            return self.unknown()
