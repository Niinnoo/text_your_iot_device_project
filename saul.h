/** 
* @{ 
*  Header file for Saul      
*
* @authors Clemens Friesl <clemens.friesl@stud.fra-uas>; 
           Nino Zoric     <nino.zoric@stud.fra-uas,de>; 
           Paul Lakus     <paul.lakus@stud.fra-uas.de>
* @}
*/

#include "saul_reg.h"

#define INTERNAL_TEMP_SENSOR_BUF_SIZE 11 
#define EXTERNAL_TEMP_SENSOR_BUF_SIZE 8
#define EXTERNAL_HUM_SENSOR_BUF_SIZE 8

/* 
    Prints temperature value to the terminal
*/
void print_temp_sensor(void);

/*
    Formats temperature sensor values of type phydat_t and writes them into a buffer
*/
void phydat_to_buffer(phydat_t *data, uint8_t dim, char *buffer, size_t buf_size);

/*
    Reads temperature sensor and writes formatted values into a buffer
*/
int8_t get_temp_sensor_formatted(char* buffer, size_t buf_size);

/*
    Reads the DHT11 sensor
*/
int8_t read_dht_sensor(char* temp_fmt, char* hum_fmt);


/*
    Prints DHT11 sensor values to the terminal
*/
int print_dht_sensor_val(int argc, char **argv);

/*
    Function that can be bound to the terminal to output the internal temperature sensor value
*/
int saul_test(int argc, char **argv);

/*
    Get function to retrieve the formatted temperature value of the DHT11 sensor
*/
int8_t get_dht_temp(char* temp_fmt);

/*
    Get function to retrieve the formatted humidity value of the DHT11 sensor
*/
int8_t get_dht_hum(char* hum_fmt);
