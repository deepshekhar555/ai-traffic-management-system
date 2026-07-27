/*
  TraffixAI - Arduino / ESP32 Smart City Traffic Signal & Hardware Controller
  Official Microcontroller Firmware for SIH 2026

  Hardware Supported:
  - Traffic Signal LEDs (Lane 1 & Lane 2 Red/Yellow/Green)
  - Servo Motor Barrier Gate (Pin 8)
  - Piezo Alarm Buzzer & Strobe Relay (Pin 9)
  - I2C SSD1306 OLED Display (0x3C SDA/SCL) for Junction Status & Signal Timer
  - VMS (Variable Message Sign) Serial Driver
  - MQ-135 Environmental Air Quality / Gas Sensor (Pin A0)
  - HC-SR04 Ultrasonic Vehicle Proximity Sensor (Pins 10 & 11)
*/

#include <Wire.h>
#include <Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Pin Definitions
const int L1_RED = 2;
const int L1_YELLOW = 3;
const int L1_GREEN = 4;

const int L2_RED = 5;
const int L2_YELLOW = 6;
const int L2_GREEN = 7;

const int SERVO_PIN = 8;
const int BUZZER_PIN = 9;

const int ULTRASONIC_TRIG = 10;
const int ULTRASONIC_ECHO = 11;
const int MQ135_PIN = A0;

Servo barrierGate;

// System States
String l1_state = "RED";
String l2_state = "RED";
bool alarm_active = false;
bool gate_open = false;
String vms_message = "TRAFFIX-AI ACTIVE";

void setup() {
  Serial.begin(9600);

  // Setup Pin Modes
  pinMode(L1_RED, OUTPUT);
  pinMode(L1_YELLOW, OUTPUT);
  pinMode(L1_GREEN, OUTPUT);

  pinMode(L2_RED, OUTPUT);
  pinMode(L2_YELLOW, OUTPUT);
  pinMode(L2_GREEN, OUTPUT);

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);

  barrierGate.attach(SERVO_PIN);
  barrierGate.write(0); // Gate closed

  // Initial LED State
  digitalWrite(L1_RED, HIGH);
  digitalWrite(L2_RED, HIGH);

  // Initialize OLED Display
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 10);
    display.println(F("TRAFFIX-AI EDGE"));
    display.setCursor(10, 25);
    display.println(F("HARDWARE ACTIVE"));
    display.display();
  }

  Serial.println("SYSTEM_READY");
}

void loop() {
  // Read PySerial Commands from Python Edge Backend
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    parseCommand(command);
  }

  // Periodic Telemetry Reporting (Air Quality & Proximity)
  static unsigned long lastReport = 0;
  if (millis() - lastReport > 2000) {
    lastReport = millis();
    reportTelemetry();
    updateOLED();
  }
}

void parseCommand(String cmd) {
  if (cmd.startsWith("L1:")) {
    if (cmd.indexOf("GREEN") != -1) setL1("GREEN");
    else if (cmd.indexOf("YELLOW") != -1) setL1("YELLOW");
    else setL1("RED");

    if (cmd.indexOf("L2:GREEN") != -1) setL2("GREEN");
    else if (cmd.indexOf("L2:YELLOW") != -1) setL2("YELLOW");
    else setL2("RED");
  } 
  else if (cmd == "ALARM:ON") {
    alarm_active = true;
    digitalWrite(BUZZER_PIN, HIGH);
  } 
  else if (cmd == "ALARM:OFF") {
    alarm_active = false;
    digitalWrite(BUZZER_PIN, LOW);
  } 
  else if (cmd == "GATE:OPEN") {
    gate_open = true;
    barrierGate.write(90);
  } 
  else if (cmd == "GATE:CLOSE") {
    gate_open = false;
    barrierGate.write(0);
  }
  else if (cmd.startsWith("VMS:")) {
    vms_message = cmd.substring(4);
  }
}

void setL1(String state) {
  l1_state = state;
  digitalWrite(L1_RED, LOW);
  digitalWrite(L1_YELLOW, LOW);
  digitalWrite(L1_GREEN, LOW);

  if (state == "GREEN") digitalWrite(L1_GREEN, HIGH);
  else if (state == "YELLOW") digitalWrite(L1_YELLOW, HIGH);
  else digitalWrite(L1_RED, HIGH);
}

void setL2(String state) {
  l2_state = state;
  digitalWrite(L2_RED, LOW);
  digitalWrite(L2_YELLOW, LOW);
  digitalWrite(L2_GREEN, LOW);

  if (state == "GREEN") digitalWrite(L2_GREEN, HIGH);
  else if (state == "YELLOW") digitalWrite(L2_YELLOW, HIGH);
  else digitalWrite(L2_RED, HIGH);
}

void updateOLED() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  display.setCursor(0, 0);
  display.print(F("L1: ")); display.print(l1_state);
  display.print(F(" | L2: ")); display.println(l2_state);
  
  display.setCursor(0, 16);
  display.print(F("Gate: ")); display.print(gate_open ? "OPEN" : "CLOSED");
  display.print(F(" | Alarm: ")); display.println(alarm_active ? "ON" : "OFF");

  display.setCursor(0, 34);
  display.println(F("--- VMS MATRIX ---"));
  display.setCursor(0, 48);
  display.println(vms_message);
  
  display.display();
}

void reportTelemetry() {
  int air_quality_raw = analogRead(MQ135_PIN);
  float co2_estimate_ppm = (air_quality_raw / 1024.0) * 800.0 + 350.0;

  // Measure Ultrasonic Distance
  digitalWrite(ULTRASONIC_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG, LOW);
  long duration = pulseIn(ULTRASONIC_ECHO, HIGH, 20000);
  float distance_cm = (duration > 0) ? (duration * 0.0343 / 2.0) : 400.0;

  Serial.print("TELEMETRY:");
  Serial.print("CO2:"); Serial.print(co2_estimate_ppm);
  Serial.print(",DIST:"); Serial.print(distance_cm);
  Serial.print(",L1:"); Serial.print(l1_state);
  Serial.print(",L2:"); Serial.println(l2_state);
}
