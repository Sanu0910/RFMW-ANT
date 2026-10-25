/* SPS-24G-01  Smart Presence Sensor Switch  -  SAMAY ELECTRONICS
 * Reference firmware for ATtiny13A (avr-gcc). Not safety-certified; validate on hardware.
 *
 * Behaviour:
 *   - Radar OUT (PB4) HIGH => person present -> lamp ON immediately (zero-cross opto).
 *   - When presence clears, start an OFF delay set by the RV1 trimmer (ADC3 on PB3), 10 s .. 10 min.
 *   - If presence returns before the delay expires, the timer is reset (lamp stays on).
 *   - Button (PB2, active-low): short press toggles Auto/Manual; in Manual, press toggles lamp ON/OFF;
 *     long press (>0.8 s) forces lamp OFF and returns to Auto.
 *   - Status LED (PB1): solid=lamp on (presence), slow blink=Manual, fast blink=fault (radar stuck).
 *   - Power-on: lamp OFF, Auto mode.
 *
 * Build (example):
 *   avr-gcc -mmcu=attiny13a -DF_CPU=1200000UL -Os -o main.elf main.c && avr-objcopy -O ihex main.elf main.hex
 *   avrdude -c usbasp -p t13 -U flash:w:main.hex    (program via J2, MAINS DISCONNECTED)
 *   Fuses: internal RC; BOD 2.7 V recommended.
 */
#include <avr/io.h>
#include <util/delay.h>
#include "board_pins.h"

#define TICK_MS        20U
static unsigned long ms = 0;

static void io_init(void) {
    DDRB  = (1 << TRIAC_PIN) | (1 << LED_PIN);          /* outputs */
    PORTB = (1 << BUTTON_PIN);                          /* (external 10k pull-up fitted; keep internal off-path) */
    /* ADC: VCC ref, input ADC3 (PB3) */
    ADMUX  = 0x03;                                      /* MUX=ADC3, REFS=VCC */
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1); /* enable, /64 */
}

static unsigned read_delay_adc(void) {
    ADCSRA |= (1 << ADSC);
    while (ADCSRA & (1 << ADSC)) { }
    return ADC;                                         /* 0..1023 */
}

/* Map ADC 0..1023 -> 10..600 seconds (roughly logarithmic feel via squared term) */
static unsigned long delay_seconds(void) {
    unsigned long a = read_delay_adc();
    return 10UL + (a * a) * 590UL / (1023UL * 1023UL);
}

static unsigned char radar_present(void) { return (PINB >> RADAR_OUT_PIN) & 1; }
static unsigned char button_down(void)   { return !((PINB >> BUTTON_PIN) & 1); }
static void lamp(unsigned char on)       { if (on) PORTB |= (1 << TRIAC_PIN); else PORTB &= ~(1 << TRIAC_PIN); }
static void led(unsigned char on)        { if (on) PORTB |= (1 << LED_PIN);   else PORTB &= ~(1 << LED_PIN); }

int main(void) {
    io_init();
    unsigned char lamp_on = 0, manual = 0, man_lamp = 0;
    unsigned long off_at = 0;              /* ms timestamp to turn off (0 = not counting) */
    unsigned long btn_t0 = 0; unsigned char btn_prev = 0, longdone = 0;
    unsigned long last_change = 0; unsigned char last_radar = 0;  /* fault heuristic */

    lamp(0); led(0);

    for (;;) {
        _delay_ms(TICK_MS);
        ms += TICK_MS;

        unsigned char present = radar_present();
        if (present != last_radar) { last_radar = present; last_change = ms; }
        unsigned char fault = (ms - last_change) > RADAR_FAULT_MS;   /* OUT never changes -> suspect radar */

        /* ---- button edge / long-press ---- */
        unsigned char b = button_down();
        if (b && !btn_prev) { btn_t0 = ms; longdone = 0; }
        if (b && !longdone && (ms - btn_t0) > LONGPRESS_MS) {        /* long press: force OFF, back to Auto */
            manual = 0; man_lamp = 0; lamp_on = 0; off_at = 0; longdone = 1;
        }
        if (!b && btn_prev && !longdone) {                          /* short press on release */
            if (!manual) { manual = 1; man_lamp = lamp_on; }        /* enter Manual, hold current */
            else         { man_lamp = !man_lamp; }                  /* toggle in Manual */
        }
        btn_prev = b;

        /* ---- control law ---- */
        if (manual) {
            lamp_on = man_lamp;
        } else {
            if (present) { lamp_on = 1; off_at = 0; }               /* present -> on, cancel timer */
            else if (lamp_on && off_at == 0) { off_at = ms + delay_seconds() * 1000UL; }  /* just left -> arm */
            else if (lamp_on && (long)(ms - off_at) >= 0) { lamp_on = 0; off_at = 0; }     /* timer expired */
        }
        if (fault) lamp_on = 0;                                     /* fail-safe OFF */

        lamp(lamp_on);

        /* ---- LED: solid=on, slow blink=manual, fast blink=fault ---- */
        if (fault)        led((ms / 100) & 1);
        else if (manual)  led((ms / 500) & 1);
        else              led(lamp_on);
    }
}
