
#include "I2Cdev.h"
#include "MPU6050.h" 


MPU6050 mpu;


#define OUTPUT_READABLE_ACCELGYRO
const int SDA_PIN = 1;
const int SCL_PIN = 0;
int16_t ax, ay, az;
int16_t gx, gy, gz;
bool blinkState; 

void setup() {

#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
Wire.begin(SDA_PIN, SCL_PIN);
  #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
  #endif 

Serial.begin(38400); 


Serial.println("Initializing MPU...");
mpu.initialize();
Serial.println("Testing MPU6050 connection...");
if(mpu.testConnection() ==  false){
Serial.println("MPU6050 connection failed");
while(true);
}
else{
Serial.println("MPU6050 connection successful");
} 


Serial.println("Updating internal sensor offsets...\n");
mpu.setXAccelOffset(0); 
mpu.setYAccelOffset(0);
mpu.setZAccelOffset(0); 
mpu.setXGyroOffset(0); 
mpu.setYGyroOffset(0);  
mpu.setZGyroOffset(0); 

Serial.print("\t");
Serial.print(mpu.getXAccelOffset());
Serial.print("\t");
Serial.print(mpu.getYAccelOffset());
Serial.print("\t");
Serial.print(mpu.getZAccelOffset());
Serial.print("\t");
Serial.print(mpu.getXGyroOffset());
Serial.print("\t");
Serial.print(mpu.getYGyroOffset());
Serial.print("\t");
Serial.print(mpu.getZGyroOffset());
Serial.print("\n"); 

} 

void loop() {
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  
  Serial.print(ax);
  Serial.print('\t');
  Serial.print(ay);
  Serial.print('\t');
  Serial.print(az);
  Serial.print('\t');
  Serial.print(gx);
  Serial.print('\t');
  Serial.print(gy);
  Serial.print('\t');
  Serial.println(gz);