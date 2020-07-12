#include <Adafruit_NeoPixel.h>
#include "DigiKeyboard.h"

const uint8_t NEO_PIN = 0; // board has this as P0
const uint8_t TONE_PIN = 1; // board has this as P1
const uint8_t NUM_PIXELS = 29;
const uint8_t BATTERY_PIN = A1; // same as P2 (correct on board)
const uint8_t PULSE_PIN = A2; // Connects to the Pi
const uint16_t BATTERY_THRESHOLD = 630;

uint16_t battery_voltage = 850; // Initial placeholder

//Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_PIXELS, NEO_PIN, NEO_GRB + NEO_KHZ800);

const uint8_t low_battery_color[3] = {255, 0, 30};
//const uint8_t[3]

void setup() {
  pinMode(BATTERY_PIN, INPUT);
  pinMode(NEO_PIN, OUTPUT);
  //pinMode(PULSE_PIN, INPUT);
  //pinMode(TONE_PIN, OUTPUT); // Not required, I guess...
  //strip.begin();
  //strip.clear();
  //strip.show();

  DigiKeyboard.sendKeyStroke(0);
  analogWrite(NEO_PIN, 127); // ~2000us wavelength with default PWM freq... I think?
}

void loop() { //20kHz means a 50us wavelength
  //if (analogRead(BATTERY_PIN) < BATTERY_THRESHOLD) {
    //dual_color_sweep(60, 150, 54612, 65535); // From pink to red
  //} else {
    uint32_t pulse_length = pulseIn(BATTERY_PIN, HIGH, 10000000L);
    DigiKeyboard.print("Length: ");
    DigiKeyboard.println(pulse_length);
    /*strip.clear();
    for (int i = 0; i < pulse_length; i++) {
      if (i < NUM_PIXELS) {
        strip.setPixelColor(i, strip.Color(0, 80, 0));
      }
    }
    strip.show();*/

    
    //switch(pulseIn(PULSE_PIN, LOW)) {
    //  case 0 ... 
    //}
    //dual_color_sweep(60, 150, 21845, 43690); // From green to blue
    //rainbow_sweep(60, 75);
  //}
  
  //delay(200); // Uncomment for smoother loops in the end
}
/*
void pulse_loop(uint8_t d, uint8_t brightness) {
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.clear();
    strip.setPixelColor(i, get_color(low_battery_color, brightness / 5));
    strip.setPixelColor((i + 1 >= NUM_PIXELS) ? (i + 1 - NUM_PIXELS) : (i + 1), get_color(low_battery_color, brightness / 2));
    strip.setPixelColor((i + 2 >= NUM_PIXELS) ? (i + 2 - NUM_PIXELS) : (i + 2), get_color(low_battery_color, brightness));
    strip.setPixelColor((i + 3 >= NUM_PIXELS) ? (i + 3 - NUM_PIXELS) : (i + 3), get_color(low_battery_color, brightness / 2));
    strip.setPixelColor((i + 4 >= NUM_PIXELS) ? (i + 4 - NUM_PIXELS) : (i + 4), get_color(low_battery_color, brightness / 5));
    strip.show();
    delay(d);
  }
}

void rainbow_sweep(uint8_t d, uint8_t brightness) {
  for (int j = 0 ; j < NUM_PIXELS; j++) {
    for (int i = 0; i < NUM_PIXELS; i++) {
      uint16_t hue = ((j + i) * (65536 / NUM_PIXELS)) % 65536;
      strip.setPixelColor(i, strip.ColorHSV(hue, 255, brightness));
    }
    strip.show();
    delay(d);
  }
}

void dual_color_sweep(uint8_t d, uint8_t brightness, int32_t min_val, int32_t max_val) {
  uint8_t x = 1;
  int32_t range = max_val - min_val;
  
  for (int j = 0 ; j < NUM_PIXELS; j++) {
    for (int i = 0; i < NUM_PIXELS; i++) {
      int32_t hue = ((j + i) * ((range * 2) / NUM_PIXELS)) % (range * 2);
      hue -= range;
      if (hue < 0) hue = map(hue, -range, -1, max_val, min_val);
      else hue = map(hue, 0, range - 1, min_val, max_val);
      for (uint8_t i = 0; i < map(abs(hue - (min_val + range / 2)), 0, range / 2, 0, 8); i++) x *= 2;
      strip.setPixelColor(i, strip.ColorHSV(hue, 255, brightness - map(x, 0, 256, brightness - 15, 0)));

      //strip.setPixelColor(i, strip.ColorHSV(hue, 255, brightness - map(abs(j - 14), 0, 14, brightness - 10, 0)));
      x = 1;
    }
    strip.show();
    delay(d);
  }
}

uint32_t get_color(const uint8_t rgb[], uint8_t brightness) {
  return strip.Color(map(rgb[0], 0, 255, 0, brightness), map(rgb[1], 0, 255, 0, brightness), map(rgb[2], 0, 255, 0, brightness));
}*/
