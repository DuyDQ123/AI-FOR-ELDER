// User_Setup.h for ESP32-2432S028R with ST7789 Driver
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

// ESP32-2432S028R uses ST7789 driver (NOT ILI9341)
#define ST7789_DRIVER      // Generic driver for ST7789

// Comment out other drivers
//#define ILI9341_DRIVER
//#define ILI9488_DRIVER
//#define ILI9342_DRIVER

// For ST7789 displays, define the pixel width and height in portrait orientation
#define TFT_WIDTH  240
#define TFT_HEIGHT 320

// For ST7789 only, define the colour order IF the blue and red are swapped on your display
// Try ONE option at a time to find the correct colour order for your display
#define TFT_RGB_ORDER TFT_RGB  // Colour order Red-Green-Blue
//#define TFT_RGB_ORDER TFT_BGR  // Colour order Blue-Green-Red

// ##################################################################################
//
// Section 2. Define the pins used for the ESP32-2432S028R
//
// ##################################################################################

// ESP32-2432S028R pin configuration
#define TFT_MISO 12  // Data out pin (SPI MISO)
#define TFT_MOSI 13  // SPI MOSI
#define TFT_SCLK 14  // SPI SCLK
#define TFT_CS   15  // Chip select control pin
#define TFT_DC   2   // Data Command control pin
#define TFT_RST  4   // Reset pin
#define TFT_BL   21  // LED back-light

// Touch screen pins
#define TOUCH_CS 33

// ##################################################################################
//
// Section 3. Define the fonts that are to be used here
//
// ##################################################################################

#define LOAD_GLCD   // Font 1. Original Adafruit 8 pixel font needs ~1820 bytes in FLASH
#define LOAD_FONT2  // Font 2. Small 16 pixel high font, needs ~3534 bytes in FLASH, 96 characters
#define LOAD_FONT4  // Font 4. Medium 26 pixel high font, needs ~5848 bytes in FLASH, 96 characters
#define LOAD_FONT6  // Font 6. Large 48 pixel high font, needs ~2666 bytes in FLASH, only characters 1234567890:-.apm
#define LOAD_FONT7  // Font 7. 7 segment 48 pixel high font, needs ~2438 bytes in FLASH, only characters 1234567890:-.
#define LOAD_FONT8  // Font 8. Large 75 pixel high font needs ~3256 bytes in FLASH, only characters 1234567890:-.
#define LOAD_GFXFF  // FreeFonts. Include access to the 48 Adafruit_GFX free fonts FF1 to FF48 and custom fonts

#define SMOOTH_FONT

// ##################################################################################
//
// Section 4. Other options
//
// ##################################################################################

// For ST7789, ST7735 and ILI9163 ONLY, define the colour order IF the blue and red are swapped on your display
// Try ONE option at a time to find the correct colour order for your display

//  #define TFT_RGB_ORDER TFT_RGB  // Colour order Red-Green-Blue
//  #define TFT_RGB_ORDER TFT_BGR  // Colour order Blue-Green-Red

// For ST7789 displays, uncomment the following line if the display is 240x240
// #define CGRAM_OFFSET

// SPI frequency
#define SPI_FREQUENCY  27000000  // 27MHz for ST7789
//#define SPI_FREQUENCY  20000000  // Try this if 27MHz doesn't work
//#define SPI_FREQUENCY  40000000  // Higher frequency (try last)

// Optional reduced SPI frequency for reading TFT
#define SPI_READ_FREQUENCY  20000000

// Touch screen SPI frequency
#define SPI_TOUCH_FREQUENCY  2500000

// ##################################################################################
//
// Section 5. Other library options
//
// ##################################################################################

// For ESP32 ONLY, comment out the next #define if you do not want to use DMA
#define ESP32_DMA_CHANNEL 1

// Support transactions automatically enabled for ESP32
#define SUPPORT_TRANSACTIONS

#endif // USER_SETUP_H