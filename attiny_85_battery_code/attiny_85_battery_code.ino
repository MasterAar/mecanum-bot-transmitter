#include <Adafruit_NeoPixel.h>

/*
   FOR UNO 5V SIGNALS:
   0% duty cycle: 0-60
   25% duty cycle: 110-400
   50% duty cycle: 401-670
   75% duty cycle: 671-950
   100% duty cycle: 950+

   FOR PI 3V3 SIGNALS:
   0% duty cycle: 0
   33% duty cycle: 200-270
   66% duty cycle: 400-480
   100% duty cycle: 679

   HSV VALUES:
   green=21845
   blue=43690
   skyblue=35134
   pink=54612
   red=65535
*/
const uint8_t NEO_PIN = 0; // board has this as P0
const uint8_t TONE_PIN = 1; // board has this as P1
const uint8_t NUM_PIXELS = 29;
const uint8_t BATTERY_PIN = A3; // same as P3 (TODO: SWITCH THIS!!!)
const uint8_t PI_PIN = A2; // Connects to the Pi
const uint16_t BATTERY_THRESHOLD = 650;
const uint8_t LOADING_COLOR[3] = {255, 100, 0};
const uint8_t ERROR_COLOR[3] = {255, 0, 0};
const uint16_t PI_VAL_LIMITS[4] = {60, 400, 670, 950};

uint16_t battery_voltage = 850; // Initial placeholder @ 4.2V
uint16_t pi_val = 0;
uint8_t pi_counter = 0;
bool shutdown_marker = false;
uint8_t prev_led_mode = -1;
uint8_t led_mode = -1;

Adafruit_NeoPixel strip = Adafruit_NeoPixel(NUM_PIXELS, NEO_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  pinMode(BATTERY_PIN, INPUT);
  pinMode(NEO_PIN, OUTPUT);
  pinMode(PI_PIN, INPUT);
  pinMode(TONE_PIN, OUTPUT); // Not required, I guess...
  strip.begin();
  strip.clear();
  strip.show();

}

void loop() {
  if (analogRead(BATTERY_PIN) < BATTERY_THRESHOLD) {
    dual_color_sweep(150, 54612, 65535); // From pink to red
  } else {
    switch (led_mode) {
      case 0: // Boot/loading
        pulse_loop(255, LOADING_COLOR); // Pulsing orange
        break;
      case 1: // Enabled
        rainbow_sweep(200); // Rainbow explosions
        break;
      case 2: // Connecting
        dual_color_sweep(230, 35134, 43690); // From sky-blue to blue
        break;
      case 3: // Calibration
        dual_color_sweep(230, 21800, 21900); // Just a dual-pulsing green
        break;
      default: // Some error
        pulse_loop(70, LOADING_COLOR); // Pulsing orange (will run 1 loop on startup)
    }
  }
}

void pulse_loop(uint8_t brightness, const uint8_t color[]) {
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.clear();
    strip.setPixelColor(i, get_color(color, brightness / 5));
    strip.setPixelColor((i + 1 >= NUM_PIXELS) ? (i + 1 - NUM_PIXELS) : (i + 1), get_color(color, brightness / 2));
    strip.setPixelColor((i + 2 >= NUM_PIXELS) ? (i + 2 - NUM_PIXELS) : (i + 2), get_color(color, brightness));
    strip.setPixelColor((i + 3 >= NUM_PIXELS) ? (i + 3 - NUM_PIXELS) : (i + 3), get_color(color, brightness / 2));
    strip.setPixelColor((i + 4 >= NUM_PIXELS) ? (i + 4 - NUM_PIXELS) : (i + 4), get_color(color, brightness / 5));
    strip.show();

    for (int k = 0; k < 10; k++)
      if (update_pi_val()) goto skip_loop;
  }
skip_loop:
  prev_led_mode = led_mode;
}

void rainbow_sweep(uint8_t brightness) {
  for (int j = 0 ; j < NUM_PIXELS; j++) {
    for (int i = 0; i < NUM_PIXELS; i++) {
      uint16_t hue = ((j + i) * (65536 / NUM_PIXELS)) % 65536;
      strip.setPixelColor(i, strip.ColorHSV(hue, 255, brightness));
    }
    strip.show();

    for (int k = 0; k < 15; k++)
      if (update_pi_val()) goto skip_loop;
  }
skip_loop:
  prev_led_mode = led_mode;
}

void dual_color_sweep(uint8_t brightness, int32_t min_val, int32_t max_val) {
  uint8_t x = 1;
  int32_t range = max_val - min_val;

  for (int j = 0 ; j < NUM_PIXELS; j++) {
    for (int i = 0; i < NUM_PIXELS; i++) {
      int32_t hue = ((j + i) * ((range * 2) / NUM_PIXELS)) % (range * 2);
      hue -= range;
      if (hue < 0) hue = map(hue, -range, -1, max_val, min_val);
      else hue = map(hue, 0, range - 1, min_val, max_val);
      for (uint8_t l = 0; l < map(abs(hue - (min_val + range / 2)), 0, range / 2, 0, 8); l++) x *= 2;
      strip.setPixelColor(i, strip.ColorHSV(hue, 255, brightness - map(x, 0, 256, brightness - 15, 0)));

      //strip.setPixelColor(i, strip.ColorHSV(hue, 255, brightness - map(abs(j - 14), 0, 14, brightness - 10, 0)));
      x = 1;
    }
    strip.show();

    for (int k = 0; k < 10; k++)
      if (update_pi_val()) goto skip_loop;
  }
skip_loop:
  prev_led_mode = led_mode;
}

uint32_t get_color(const uint8_t rgb[], uint8_t brightness) {
  return strip.Color(map(rgb[0], 0, 255, 0, brightness), map(rgb[1], 0, 255, 0, brightness), map(rgb[2], 0, 255, 0, brightness));
}

bool update_pi_val() {
  if (pi_counter == 0) pi_val = 0;

  pi_val += analogRead(PI_PIN);
  delay(4);
  pi_counter++;

  if (pi_counter > 30) { // Multiples of (60 / delay) are preferred
    pi_counter = 0;

    prev_led_mode = led_mode;

    switch (pi_val / 30) { // Same as the number 3 lines above this
      case 0 ... 20: // 0
        led_mode = 0;
        break;
      case 21 ... 335: // 235
        led_mode = 1;
        break;
      case 336 ... 630: // 440
        led_mode = 2;
        break;
      default: // 697 (3V3 theoretical maximum is 676)
        led_mode = 3;
    }

    if (prev_led_mode == 3 && led_mode == 0) {
      shutdown_marker = true;
      return true;
    } else if (prev_led_mode != led_mode) {
      return true;
    } else if (shutdown_marker && led_mode == 0) {
      strip.clear();
      for (int i = 0; i < NUM_PIXELS; i++) strip.setPixelColor(i, get_color(LOADING_COLOR, 170));
      strip.show();
      delay(6000);
      strip.clear();
      strip.show();
      while (true) {
        delay(1000);
      }
    }

  }
  return false;
}
