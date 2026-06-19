/*
  NOTE: PLS READ THE SETUP FOR INSTRUCTIONS BEFORE RUNNING, OR IT WILL NOT WORK!!!

  Bad Apple!! buts its on the Serial plotter

  (Needs SD card to store video data)

  Works on a Teensy 4.1 (uses its built-in SD slot) and on any other board with an SPI SD
  card module. If the board is not a Teensy 4.1 it defaults to an SPI SD module on SD_CS_PIN.

  by Jason S

  Github: https://github.com/shenjason


  Common Issues:

  if seeing "SD Card initialization failed!" try disconnecting and reconnecting and should work
  if not seeing any output, then try rebooting Serial plotter, Check the if the Serial plotter is stopped, or send a message (can be anything)
  if is any error regarding file, try replacing the video file in the SD card with a new example copy
*/


#include <Arduino.h>
#include <SD.h>

//Why did I make ts :( I'm wasting my time


#define VID_HEIGHT 37 //Change this if used a different height than the provided video files
#define VID_WIDTH 50 //Has to stay to 50 due to Serial plotter only display 50 past values (unless its some legacy Serial plotter that has a diff value)

//SD card chip-select pin used when NOT on a Teensy 4.1 (generic SPI SD module)
//Change this to match your wiring
#define SD_CS_PIN 5


float frameInterval;
int currentFrameNum = 0;
bool firstFrame = true;
int starting_millis;

char currentFrame[VID_WIDTH*VID_HEIGHT + 5];

File video;

void setup() {
  Serial.begin(230400);

#if defined(ARDUINO_TEENSY41)
  bool sdGood = SD.begin(BUILTIN_SDCARD);
#else
  bool sdGood = SD.begin(SD_CS_PIN);       
#endif
  if (!sdGood) {
    Serial.println("SD Card initialization failed!");
    while (1);
  }

  video = SD.open("badapple.plot", FILE_READ);
  if (!video) { 
    Serial.println("Video File missing or incorrect file name!"); 
    while (1);
  }

  int width; int frames; int fps; int height;
  String header = video.readStringUntil('\n');
  if (sscanf(header.c_str() , "%d %d %d %d", &width, &height, &frames, &fps) < 4){
    Serial.println("Broken File Header!");
    while (1);
  }

  if (height != VID_HEIGHT){
    Serial.println("Invalid Vid Height!");
    while (1);
  }

  if (width != VID_WIDTH){
    Serial.println("Invalid Vid Width!");
    while (1);
  }
  frameInterval = 1000.0 / fps;
  

  if (video.available()) {
    video.readBytesUntil('~', currentFrame, sizeof(currentFrame));
    video.read();
  }

  Serial.println("Press any key to start...");
  while (!Serial.available());

  starting_millis = millis();

}

void loop() {
  if (millis() - starting_millis >= frameInterval * currentFrameNum) {
      printFrame();
      currentFrameNum++;


      if (video.available()) {
        video.readBytesUntil('~', currentFrame, sizeof(currentFrame));
        video.read();
      }else{
        Serial.print("\n\n\n\n\n\n\n");
        Serial.println("END");
        video.close();
        while (1);
      }
  }
}

void printFrame() {

  for (int x = 0; x < VID_WIDTH; x++) {
    for (int y = 0; y < VID_HEIGHT; y++) { 
      int point = (int)(currentFrame[x +  y * VID_WIDTH]) - 34;
      
      Serial.print(' '); Serial.print(y);
      
      Serial.print(':'); 

      if (point < 0 || point >= VID_HEIGHT){
        Serial.print(NAN);
      }else{Serial.print(point);} 
    }
    Serial.print(" L:0 H:"); Serial.print(VID_HEIGHT);
    Serial.println();
  }
  
} 
  

