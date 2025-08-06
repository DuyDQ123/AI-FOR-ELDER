// User_Setup.h for ESP32-2432S028R (2.8" TFT Touch Display)
// Copy this content to replace User_Setup.h in TFT_eSPI library

#ifndef USER_SETUP_H
#define USER_SETUP_H

// ##################################################################################
//
// Section 1. Call up the right driver file and any options for it
//
// ##################################################################################

// Define to disable all #warnings in library
//#define DISABLE_ALL_LIBRARY_WARNINGS

// ESP32-2432S028R typically uses ILI9341 or ST7789
// Try these drivers one by one:

// Option 1: ILI9341 (most common)
#define ILI9341_DRIVER

// If ILI9341 doesn't work, comment above and try:
//#define ST7789_DRIVER
//#define ILI9488_DRIVER
//#define ILI9342_DRIVER

// ##################################################################################
//
// Section 2. Define the display driver, this must be commented out to use a
//            default driver
//
// ##################################################################################

// ESP32-2432S028R pin configuration
#define TFT_MISO 12  // ESP32-2432S028R specific
#define TFT_MOSI 13  // ESP32-2432S028R specific  
#define TFT_SCLK 14  // ESP32-2432S028R specific
#define TFT_CS   15  // Chip select control pin
#define TFT_DC   2   // Data Command control pin
#define TFT_RST  4   // Reset pin
#define TFT_BL   21  // LED back-light (Very important!)

// Touch screen pins for ESP32-2432S028R
#define TOUCH_CS 33

// Alternative pin configuration if above doesn't work:
// Uncomment these and comment above if needed
//#define TFT_MISO 19
//#define TFT_MOSI 23
//#define TFT_SCLK 18
//#define TFT_CS   15
//#define TFT_DC   2
//#define TFT_RST  4
//#define TFT_BL   21

// ##################################################################################
//
// Section 3. Define the fonts that are to be used here
//
// ##################################################################################

// Comment out the #defines below with // to stop that font being loaded
#define LOAD_GLCD   // Font 1. Original Adafruit 8 pixel font needs ~1820 bytes in FLASH
#define LOAD_FONT2  // Font 2. Small 16 pixel high font, needs ~3534 bytes in FLASH, 96 characters
#define LOAD_FONT4  // Font 4. Medium 26 pixel high font, needs ~5848 bytes in FLASH, 96 characters
#define LOAD_FONT6  // Font 6. Large 48 pixel high font, needs ~2666 bytes in FLASH, only characters 1234567890:-.apm
#define LOAD_FONT7  // Font 7. 7 segment 48 pixel high font, needs ~2438 bytes in FLASH, only characters 1234567890:-.
#define LOAD_FONT8  // Font 8. Large 75 pixel high font needs ~3256 bytes in FLASH, only characters 1234567890:-.
#define LOAD_GFXFF  // FreeFonts. Include access to the 48 Adafruit_GFX free fonts FF1 to FF48 and custom fonts

// Comment out the #define below to stop the SPIFFS filing system and smooth font code being loaded
#define SMOOTH_FONT

// ##################################################################################
//
// Section 4. Other options
//
// ##################################################################################

// For ESP32 Dev board (ESP32-2432S028R)
// The hardware SPI can be mapped to any pins

// SPI frequency - try lower if display issues occur
#define SPI_FREQUENCY  27000000  // Lower frequency for stability
//#define SPI_FREQUENCY  40000000  // Try this if 27MHz works
//#define SPI_FREQUENCY  20000000  // Even lower if needed

// Optional reduced SPI frequency for reading TFT
#define SPI_READ_FREQUENCY  20000000

// The XPT2046 requires a lower SPI clock rate
#define SPI_TOUCH_FREQUENCY  2500000

// ##################################################################################
//
// Section 5. Call up the right driver file and any options for it
//
// ##################################################################################

// For ST7789 displays, uncomment the following line if the display is 240x240
// #define CGRAM_OFFSET

// For ESP32 ONLY, comment out the next #define if you do not want to use DMA with the SPI interface
#define ESP32_DMA_CHANNEL 1

// ##################################################################################
//
// Section 6. Other library options
//
// ##################################################################################

// Support for UTF8 fonts
//#define SUPPORT_UTF8_UNICODE

// Smooth fonts
#define SMOOTH_FONT

// Support transactions automatically enabled for ESP32
#define SUPPORT_TRANSACTIONS

#endif // USER_SETUP_H