/** 
* @{ 
*  This file implements functions to read out sensors using the SAUL and 
*  DHT library from RIOT.
*  Parts of this program are taken from the RIOT examples.
*  Source: https://github.com/RIOT-OS/RIOT/tree/master/examples/saul        
*
* @authors Clemens Friesl <clemens.friesl@stud.fra-uas>; 
           Nino Zoric     <nino.zoric@stud.fra-uas,de>; 
           Paul Lakus     <paul.lakus@stud.fra-uas.de>
* @}
*/

#include "saul_reg.h"
#include <stdio.h>
#include "shell.h"
#include "saul.h"
#include <math.h>
#include <stdlib.h>
#include "dht.h"
#include "fmt.h"
#include "xtimer.h"


/*
    Finds the temperature sensor, reads it and formats the result
*/
int8_t get_temp_sensor_formatted(char *buffer, size_t buf_size)
{
    if (buf_size == 0 || buffer == NULL)
    {
        return -1;
    }

    saul_reg_t *tmp = saul_reg_find_type(SAUL_SENSE_TEMP);
    if (tmp == NULL)
    {
        return -2;
    }
    else
    {
        phydat_t result;
        if (saul_reg_read(tmp, &result) < 0)
        {
            return -3;
        }
        phydat_to_buffer(&result, 1, buffer, buf_size);
        return 0;
    }
}

/*
    Displays the temperature on the screen
*/
void print_temp_sensor(void)
{
    char buffer[INTERNAL_TEMP_SENSOR_BUF_SIZE];
    if (get_temp_sensor_formatted(buffer, sizeof(buffer)) == 0 && strlen(buffer) > 0)
    {
        printf("Temperatur: %s\n", buffer);
    }
    else
    {
        puts("Etwas ist schief gelaufen!");
    }
}

/*
    Converts sensor value to decimal
*/
void phydat_to_buffer(phydat_t *data, uint8_t dim, char *buffer, size_t buf_size)
{
    int offset = 0;

    // Scale
    for (uint8_t i = 0; i < dim; i++)
    {
        int scale_factor = (int)pow(10, -data->scale);
        int integer_part = data->val[i] / scale_factor;
        int fractional_part = abs(data->val[i] % scale_factor);

        int ret = snprintf(buffer + offset, buf_size - offset, "%d.%02d ", integer_part, fractional_part);
        if (ret < 0 || (size_t)ret >= buf_size - offset)
        {
            snprintf(buffer + offset, buf_size - offset, "[TRUNCATED]");
            break;
        }
        offset += ret;
    }

    // Unit
    char unit_string[5];
    phydat_unit_write(unit_string, sizeof(unit_string), data->unit);
    if (strlen(unit_string) == 0)
    {
        snprintf(buffer + offset, buf_size - offset, "%s", "unknown");
    }
    snprintf(buffer + offset, buf_size - offset, "%s", unit_string);
}

/*
    Reads the DHT11 sensor and formats the values into a readable format
*/
int8_t read_dht_sensor(char *temp_fmt, char *hum_fmt)
{
    dht_t dev;
    static const dht_params_t dht_params = {
        .type = DHT11,
        .pin = GPIO_PIN(0, 31)
    };

    if (dht_init(&dev, &dht_params) != DHT_OK)
    {
        printf("Error initializing DHT11 sensor.\n");
        return -1;
    }
    else
    {
        printf("DHT Init was successfull!\n");
    }

    int16_t temp, hum;
    while (1)
    {
        xtimer_usleep(1000000);
        if (dht_read(&dev, &temp, &hum) == DHT_OK)
        {            
            size_t fmt_length = fmt_s16_dfp(temp_fmt, temp, -1);
            temp_fmt[fmt_length] = '\0';
            fmt_length = fmt_s16_dfp(hum_fmt, hum, -1);
            hum_fmt[fmt_length] = '\0';
            return 0;
        }
        else
        {
            printf("Failed to read data from DHT11 sensor!\n");
            return -1;
        }
    }
}

/*
    Outputs the DHT11 sensor values on the terminal
*/
int print_dht_sensor_val(int argc, char **argv)
{
    char temp[EXTERNAL_TEMP_SENSOR_BUF_SIZE];
    char humidity[EXTERNAL_HUM_SENSOR_BUF_SIZE];
    if (read_dht_sensor(temp, humidity) == 0)
    {
        printf("Temperature: %s°C, Humidity: %s%%\n", temp, humidity);
        return 0;
    }
    return -1;
}


/*
    Outputs the temperature sensor values on the terminal
*/
int saul_test(int argc, char **argv)
{
    print_temp_sensor();
    return 0;
}

/*
    Get function to get the temperature value of the DHT11 sensor formatted
*/
int8_t get_dht_temp(char* temp_fmt){
    char hum[EXTERNAL_HUM_SENSOR_BUF_SIZE];
    if(read_dht_sensor(temp_fmt, hum) == 0){
        return 0;
    }
    return -1;
}

/*
   Get function to get the humidity value of the DHT11 sensor formatted
*/
int8_t get_dht_hum(char* hum_fmt){
    char temp[EXTERNAL_TEMP_SENSOR_BUF_SIZE];
    if(read_dht_sensor(temp, hum_fmt) == 0){
        return 0;
    }
    return -1;
}
