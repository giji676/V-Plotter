#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Servo.h>
#include <Wire.h>
#include <SD.h>
#include <TMCStepper.h>
#include <AccelStepper.h>
#include <MultiStepper.h>
#include <Arduino.h>
#include "wiring_private.h"

#define i2c_Address 0x3c
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SH1106G display = Adafruit_SH1106G(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define STEP_PIN_1 7
#define DIR_PIN_1 6
#define STEP_PIN_2 4
#define DIR_PIN_2 3

#define R_SENSE 0.11f
Uart mySerial (&sercom3, 20, 21, SERCOM_RX_PAD_1, UART_TX_PAD_2);

TMC2209Stepper driver1(&Serial1, R_SENSE, 0);  // Hardware serial, address 0
TMC2209Stepper driver2(&mySerial, R_SENSE, 1); // Software serial, address 1

AccelStepper stepper1(AccelStepper::DRIVER, STEP_PIN_1, DIR_PIN_1);
AccelStepper stepper2(AccelStepper::DRIVER, STEP_PIN_2, DIR_PIN_2);

MultiStepper steppers;
int maxSpeed = 3000;  // Default maxSpeed

// Rotatory encoder
const int inputCLK = 2;
const int inputDT = 8;
const int inputSW = 9;

int counter = 0;
int currentStateCLK;
int previousStateCLK;
int currentStateSW;
int encdir = 0;

Servo servoMotor;
const int servoPin = 5;
int servoPos = 0;

File file;
const int chipSelect = 10;
int highlightedFileIndex = 0;
int selectedFileIndex = 0;
int inFileSelection = true;
int numFiles = 0;

bool running = false;

void setup ()
{
  Serial.begin(9600); // For USB comms
  // while (!Serial);  // Wait for Serial connection (important on SAMD)

  Serial1.begin(115200); // Driver 1
  pinPeripheral(20, PIO_SERCOM); // RX
  pinPeripheral(21, PIO_SERCOM); // TX
  mySerial.begin(115200); // Driver 2

  Serial.println("Serials setup");
  driver1.begin();
  driver1.toff(5);
  driver1.rms_current(600);
  driver1.microsteps(16);
  driver1.en_spreadCycle(false);
  driver1.pdn_disable(true);        // Enable UART control
  driver1.I_scale_analog(false);

  driver2.begin();
  driver2.toff(5);
  driver2.rms_current(600);
  driver2.microsteps(16);
  driver2.en_spreadCycle(false);
  driver2.pdn_disable(true);
  driver2.I_scale_analog(false);

  stepper1.setMaxSpeed(maxSpeed);
  stepper2.setMaxSpeed(maxSpeed);

  steppers.addStepper(stepper1);
  steppers.addStepper(stepper2);

  Serial.println("Drivers setup");

  servoMotor.attach(servoPin);

  while (!SD.begin(chipSelect)) {
    Serial.println("SD card initialization failed!");
    digitalWrite(LED_BUILTIN, HIGH);
    delay(500);
    digitalWrite(LED_BUILTIN, LOW);
    delay(500);
  }
  Serial.println("SD card setup");

  // Rotatory encoder
  pinMode (inputCLK, INPUT);
  pinMode (inputDT, INPUT);
  pinMode (inputSW, INPUT);
  
  previousStateCLK = digitalRead(inputCLK);

  attachInterrupt(digitalPinToInterrupt(2), checkEncoderState, CHANGE);
  attachInterrupt(digitalPinToInterrupt(9), checkEncoderSwitch, RISING);

  Serial.println("Interupts setup");


  display.begin(i2c_Address, true);
  display.display();
  while (true) {
    while (inFileSelection) {
      file = SD.open("/");
      displayFiles(file);
      file.close();
    }

    file = SD.open("/");

    int fileIndex = 0;

    while (true) {
      File entry =  file.openNextFile();
      if (!entry) {
        break;
      }
      if (!entry.isDirectory()) {
        if (fileIndex == selectedFileIndex) {
          file = entry;
          break;
        }
        fileIndex ++;
      }
      entry.close();
    }
    displayText("Run");

    while (file.available()) {
      if (!running) {
        continue;
      }

      String line = file.readStringUntil('\n');
      line.trim();
      displayText(line);

      if (line.startsWith("maxSpeed:")) {
        int colonIndex = line.indexOf(":");
        if (colonIndex != -1) {
          String maxSpeedStr = line.substring(colonIndex + 1);
          maxSpeed = maxSpeedStr.toInt();
          stepper1.setMaxSpeed(maxSpeed);
          stepper2.setMaxSpeed(maxSpeed);
          Serial.print("Set maxSpeed: ");
          Serial.println(maxSpeed);
          continue;
        }
      }
      else if (line.startsWith("PENUP:")) {
        int colonIndex = line.indexOf(":");
        if (colonIndex != -1) {
          String servoPosStr = line.substring(colonIndex + 1);
          servoPos = servoPosStr.toInt();
          servoMotor.write(servoPos);
          delay(1000);
          continue;
        }
      }
      else if (line.startsWith("PENDOWN:")) {
        int colonIndex = line.indexOf(":");
        if (colonIndex != -1) {
          String servoPosStr = line.substring(colonIndex + 1);
          servoPos = servoPosStr.toInt();
          servoMotor.write(servoPos);
          delay(1000);
          continue;
        }
      }
      else if (line.startsWith("PAUSE")) {
        running = false;
        continue;
      }

      int commaIndex = line.indexOf(",");

      if (commaIndex != -1) {
        String num1Str = line.substring(0, commaIndex);
        String num2Str = line.substring(commaIndex + 1);

        int num1 = num1Str.toInt();
        int num2 = num2Str.toInt();

        long positions[2];

        positions[0] = num1;
        positions[1] = num2;
          
        steppers.moveTo(positions);
        steppers.runSpeedToPosition();
      }
    }
    while (running) {
      displayFinishScreen();
    }
    highlightedFileIndex = 0;
    selectedFileIndex = 0;
    inFileSelection = true;
    numFiles = 0;
  }
}

void displayFinishScreen() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);
  display.println(file.name());
  display.setTextColor(SH110X_BLACK, SH110X_WHITE);
  display.println("FINISH");
  display.display();
}

void displayFiles(File file) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);

  int fileIndex = 0;
  while (true) {
    if (fileIndex == highlightedFileIndex) {
      display.setTextColor(SH110X_BLACK, SH110X_WHITE);
    } else {
      display.setTextColor(SH110X_WHITE);
    }
    File entry =  file.openNextFile();
    if (!entry) {
      break;
    }

    if (!entry.isDirectory()) {
      display.println(entry.name());
      fileIndex ++;
      if (fileIndex > numFiles) {
        numFiles = fileIndex;
      }
    }
    entry.close();
  }

  display.display();
}

void displayText(String text) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);
  display.println(file.name());
  
  display.setTextColor(SH110X_BLACK, SH110X_WHITE);
  if (running) {
    display.println("Pause");
  } else {
    display.println("Resume");
  }
  display.setTextColor(SH110X_WHITE);
  display.println(text);

  display.display();
}

void checkEncoderState() {
  currentStateCLK = digitalRead(inputCLK);

  if (currentStateCLK != previousStateCLK){ 
    if (digitalRead(inputDT) != currentStateCLK) { 
      encdir = 1;
      counter += encdir;
    }
    else {
      encdir = -1;
      counter += encdir;
    }
  }
  previousStateCLK = currentStateCLK;

  if (inFileSelection) {
    highlightedFileIndex = abs(int(counter/2)) % numFiles;
  }
}

void checkEncoderSwitch() {
  currentStateSW = digitalRead(inputSW);
  if (inFileSelection) {
    selectedFileIndex = highlightedFileIndex;
    inFileSelection = false;
  } else {
    running = !running;
  }
}

void loop() {}