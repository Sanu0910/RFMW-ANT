// NOVA-RF1 board pin map (original firmware-compatible multi-tool board).
// Derived from the GPIO/peripheral assignments the open-source Flipper Zero firmware expects
// (flipperdevices/flipperzero-firmware, GPLv3, targets/f7/furi_hal/furi_hal_resources.{c,h}).
// These are the STM32WB55 pins a firmware-compatible board must wire; use this when porting firmware.
#pragma once

// ---- SPI-R (radio bus): CC1101 + ST25R3916 ----
#define MT1_SPI_R_SCK      GPIOA, 5
#define MT1_SPI_R_MISO     GPIOB, 4
#define MT1_SPI_R_MOSI     GPIOB, 5
#define MT1_CC1101_CS      GPIOD, 0    // sub-GHz radio chip select
#define MT1_CC1101_GDO0    GPIOA, 1    // sub-GHz radio interrupt / data
#define MT1_RF_SW_0        GPIOC, 4    // antenna RF switch control
#define MT1_NFC_CS         GPIOE, 4    // ST25R3916 chip select

// ---- SPI-D (display bus): display + microSD ----
#define MT1_SPI_D_SCK      GPIOD, 1
#define MT1_SPI_D_MISO     GPIOC, 2
#define MT1_SPI_D_MOSI     GPIOB, 15
#define MT1_DISPLAY_CS     GPIOC, 11
#define MT1_DISPLAY_DI     GPIOB, 1    // data/command
#define MT1_DISPLAY_RST    GPIOB, 0
#define MT1_SD_CS          GPIOC, 12
#define MT1_SD_CD          GPIOC, 10   // card detect

// ---- 125 kHz RFID analog front-end ----
#define MT1_RFID_CARRIER_OUT  GPIOA, 15   // timer carrier drive
#define MT1_RFID_CARRIER      GPIOA, 2    // carrier sense / pull (shared with NFC IRQ pull)
#define MT1_RFID_RF_IN        GPIOC, 5    // demodulated RF in (comparator)

// ---- Infrared ----
#define MT1_IR_TX          GPIOB, 9    // IR LED drive (timer, 38 kHz)
#define MT1_IR_RX          GPIOA, 0    // IR demodulator in

// ---- 1-Wire / iButton ----
#define MT1_IBUTTON        GPIOB, 14   // open-drain

// ---- Buttons (5-way + back) ----
#define MT1_BTN_UP         GPIOB, 10
#define MT1_BTN_DOWN       GPIOC, 6
#define MT1_BTN_LEFT       GPIOB, 11
#define MT1_BTN_RIGHT      GPIOB, 12
#define MT1_BTN_OK         GPIOH, 3
#define MT1_BTN_BACK       GPIOC, 13

// ---- Haptics / sound ----
#define MT1_VIBRO          GPIOA, 8
#define MT1_SPEAKER        GPIOB, 8    // PWM

// ---- Power ----
#define MT1_PERIPH_POWER   GPIOA, 3    // peripheral-rail load switch enable
#define MT1_I2C_PWR_SDA    GPIOA, 10   // fuel gauge + charger
#define MT1_I2C_PWR_SCL    GPIOA, 9

// ---- USB / debug / external UART ----
#define MT1_USB_DM         GPIOA, 11
#define MT1_USB_DP         GPIOA, 12
#define MT1_SWDIO          GPIOA, 13
#define MT1_SWCLK          GPIOA, 14
#define MT1_USART1_TX      GPIOB, 6
#define MT1_USART1_RX      GPIOB, 7

// ---- External GPIO header (user pins) ----
#define MT1_EXT_PA7        GPIOA, 7
#define MT1_EXT_PA6        GPIOA, 6
#define MT1_EXT_PA4        GPIOA, 4
#define MT1_EXT_PB3        GPIOB, 3
#define MT1_EXT_PB2        GPIOB, 2
#define MT1_EXT_PC3        GPIOC, 3
#define MT1_EXT_PC1        GPIOC, 1
#define MT1_EXT_PC0        GPIOC, 0
