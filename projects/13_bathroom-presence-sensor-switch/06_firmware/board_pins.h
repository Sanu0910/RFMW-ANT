/* SPS-24G-01  (SAMAY ELECTRONICS)  -  ATtiny13A pin map.
 * Generated to match 02_python/design.py. Fuse: internal 9.6 MHz RC, /8 off (CKDIV8=1 -> 1.2 MHz) is fine;
 * 4.8/9.6 MHz also OK. BOD at 2.7 V recommended. Program via J2 (AVR ISP) with MAINS DISCONNECTED.
 *
 * ATtiny13A SOIC-8:
 *   1 PB5/RESET   -> RESET / ISP            5 PB0/MOSI -> TRIAC_DRV (opto LED, via R1 330R) + ISP MOSI
 *   2 PB3/ADC3    -> DELAY_ADJ (trimmer)    6 PB1/MISO -> STATUS LED (D1, via R1k)          + ISP MISO
 *   3 PB4/ADC2    -> RADAR_OUT (LD2410B)    7 PB2/SCK  -> BUTTON (SW1, active-low)           + ISP SCK
 *   4 GND                                   8 VCC (+5V)
 */
#pragma once
#include <avr/io.h>

#define RADAR_OUT_PIN   PB4   /* input : HIGH = person present (LD2410B OUT, 3.3 V) */
#define DELAY_ADC_CH    3     /* ADC3 on PB3 : 10k trimmer, sets OFF delay 10 s..10 min */
#define TRIAC_PIN       PB0   /* output: HIGH = opto ON = lamp ON (zero-cross) */
#define LED_PIN         PB1   /* output: status/fault LED */
#define BUTTON_PIN      PB2   /* input : momentary override, active-low (10k pull-up on board) */

/* Timing */
#define DELAY_MIN_S      10UL      /* trimmer fully CCW  */
#define DELAY_MAX_S      600UL     /* trimmer fully CW (10 min) */
#define DEBOUNCE_MS      30
#define LONGPRESS_MS     800       /* long press = force OFF */
#define RADAR_FAULT_MS   30000UL   /* OUT stuck, no change, radar-not-responding heuristic (optional) */

/* Logic levels */
#define PRESENT          1         /* RADAR_OUT asserted level */
#define LED_ON_LEVEL     1
#define TRIAC_ON_LEVEL   1
#define BUTTON_ACTIVE    0         /* pressed = low */
