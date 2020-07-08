#include <Adafruit_NeoPixel.h>
#include "hsv.h"

const int NEO_PIN = 1;
const int TONE_PIN = 0;
const int NUM_PIXELS = 29;
const int BATTERY_PIN = A1;
const int BATTERY_THRESHOLD = 630;

int battery_voltage = 850;
int brightness = 75; // For default operation

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_PIXELS, NEO_PIN, NEO_GRB + NEO_KHZ800);

// DEFAULT LOW BATTERY COLOR
int r = 255;
int g = 0;
int b = 25;

void setup() {
  pinMode(BATTERY_PIN, INPUT);
  //pinMode(TONE_PIN, OUTPUT); // Not required, I guess...
  strip.begin();
  strip.clear();
  strip.show();
}

void loop() {
  battery_voltage = analogRead(BATTERY_PIN);

  if (battery_voltage >= BATTERY_THRESHOLD) {
    rainbow_sweep(70, brightness);
  } else {
    pulse_loop(30, 255);
    tone(TONE_PIN, 800, 1000);
    delay(1000);
    noTone(TONE_PIN);
  }
  
  delay(60);
}

void pulse_loop(int d, int brightness) {
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.clear();
    strip.setPixelColor(i, get_color(brightness / 5));
    strip.setPixelColor((i + 1 >= NUM_PIXELS) ? (i + 1 - NUM_PIXELS) : (i + 1), get_color(brightness / 2));
    strip.setPixelColor((i + 2 >= NUM_PIXELS) ? (i + 2 - NUM_PIXELS) : (i + 2), get_color(brightness));
    strip.setPixelColor((i + 3 >= NUM_PIXELS) ? (i + 3 - NUM_PIXELS) : (i + 3), get_color(brightness / 2));
    strip.setPixelColor((i + 4 >= NUM_PIXELS) ? (i + 4 - NUM_PIXELS) : (i + 4), get_color(brightness / 5));
    strip.show();
    delay(d);
  }
}

void pulse_bounce(int d, int brightness) {
  int m = 1;
  int n = 0;
  do {
    while (n >= 0 && n <= (NUM_PIXELS - 3)) {
      strip.clear();
      strip.setPixelColor(n, get_color(brightness / 3));
      strip.setPixelColor(n + 1, get_color(brightness));
      strip.setPixelColor(n + 2, get_color(brightness / 3));
      strip.show();
      delay(d);
      n += m;
    }
    m *= -1;
    n += 2 * m;
  } while (m == -1);
}

void rainbow_sweep(int d, int brightness) {
  for (int j = 0 ; j < NUM_PIXELS; j++) {
    for (int i = 0; i < NUM_PIXELS; i++) {
      uint16_t hue = ((j + i) * (65536 / NUM_PIXELS)) % 65536;
      strip.setPixelColor(i, strip.ColorHSV(hue, 255, brightness));
      //Serial.println(hue);
    }
    Serial.println("");
    strip.show();
    delay(d);
  }
}

uint32_t get_color(int multiplier) {
  return strip.Color(map(r, 0, 255, 0, multiplier), map(g, 0, 255, 0, multiplier), map(b, 0, 255, 0, multiplier));
}
