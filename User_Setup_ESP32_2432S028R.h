// USER_SETUP for ESP32-2432S028R (ESP32 with 2.8" TFT Touch Display)
// Copy this content to replace the User_Setup.h file in TFT_eSPI library folder

#ifndef USER_SETUP_H
#define USER_SETUP_H

// ##################################################################################
//
// Section 1. Call up the right driver file and any options for it
//
// ##################################################################################

// Define to disable all #warnings in library (can be put in User_Setup_Select.h)
//#define DISABLE_ALL_LIBRARY_WARNINGS

// Tell the library to use 8-bit parallel mode (ESP32 only)
//#define TFT_PARALLEL_8_BIT

// Tell the library to use the ESP32 DMA SPI port 1 or 2
//#define TFT_eSPI_ESP32_DMA

// ESP32 processors only - define the pins used
#define TFT_MISO 19
#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS   15  // Chip select control pin
#define TFT_DC   2   // Data Command control pin
#define TFT_RST  4   // Reset pin (could connect to Arduino RESET pin)
#define TFT_BL   21  // LED back-light

// Optional touch screen chip select
//#define TOUCH_CS 33     // Chip select pin (T_CS) of touch screen

// ##################################################################################
//
// Section 2. Define the display driver, this must be commented out to use a
//            default driver
//
// ##################################################################################

// Only define one driver, the other ones must be commented out
#define ILI9341_DRIVER      // Generic driver for common displays

//#define ILI9341_2_DRIVER     // Alternative ILI9341 driver, see https://github.com/Bodmer/TFT_eSPI/issues/1172
//#define ILI9342_DRIVER       // For ESP32 dev board (only tested with ILI9341 display)
//#define ILI9481_DRIVER       // WARNING: Do not connect ILI9481 display SDO to MISO if other devices share the SPI bus (TFT SDO does NOT tristate when CS is high)
//#define ILI9486_DRIVER       // WARNING: Do not connect ILI9486 display SDO to MISO if other devices share the SPI bus (TFT SDO does NOT tristate when CS is high)
//#define ILI9488_DRIVER       // WARNING: Do not connect ILI9488 display SDO to MISO if other devices share the SPI bus (TFT SDO does NOT tristate when CS is high)
//#define ST7789_DRIVER        // Full configuration option, define additional parameters below for this display
//#define ST7789_2_DRIVER      // Minimal configuration option, define additional parameters below for this display
//#define ST7735_DRIVER        // Define additional parameters below for this display
//#define ST7796_DRIVER        // Define additional parameters below for this display
//#define RM68140_DRIVER       // Define additional parameters below for this display
//#define SSD1351_DRIVER       // Define additional parameters below for this display
//#define SSD1963_480          // Untested
//#define SSD1963_800          // Untested
//#define SSD1963_800ALT       // Untested
//#define ILI9163_DRIVER       // Define additional parameters below for this display
//#define GC9A01_DRIVER        // Define additional parameters below for this display
//#define HX8357D_DRIVER       // Define additional parameters below for this display

// Some displays support SPI reads via the MISO pin, other displays have a single
// bi-directional SDA pin and the library will try to read this via the MOSI line.
// To use the SDA line for reading data from the TFT uncomment the following line:

//#define TFT_SDA_READ      // This option is for ESP32 ONLY, tested with ST7789 and GC9A01 display only

// For ST7789, ST7735, ILI9163 and GC9A01 ONLY, define the colour order IF the blue and red are swapped on your display
// Try ONE option at a time to find the correct colour order for your display

//  #define TFT_RGB_ORDER TFT_RGB  // Colour order Red-Green-Blue
//  #define TFT_RGB_ORDER TFT_BGR  // Colour order Blue-Green-Red

// For M5Stack ESP32 module with integrated ILI9341 display ONLY, remove // in line below

//#define M5STACK

// For ST7789, ST7735, ILI9163 and GC9A01 ONLY, define the pixel width and height in portrait orientation
// #define TFT_WIDTH  80
// #define TFT_WIDTH  128
// #define TFT_WIDTH  160 // ST7735
// #define TFT_WIDTH  240 // ST7789 240 x 240 and 240 x 320
// #define TFT_HEIGHT 160
// #define TFT_HEIGHT 128
// #define TFT_HEIGHT 240 // ST7789 240 x 240
// #define TFT_HEIGHT 320 // ST7789 240 x 320
// #define TFT_HEIGHT 240 // GC9A01 240 x 240

// For ST7796 ONLY, define the pixel width and height in portrait orientation
// #define TFT_WIDTH  320
// #define TFT_HEIGHT 480

// For HX8357D ONLY, define the pixel width and height in portrait orientation
// #define TFT_WIDTH  320
// #define TFT_HEIGHT 480

// For EPD displays, define the pixel width and height in portrait orientation
// #define TFT_WIDTH  128
// #define TFT_HEIGHT 296

// ##################################################################################
//
// Section 3. Define the fonts that are to be used here
//
// ##################################################################################

// Comment out the #defines below with // to stop that font being loaded
// The ESP8266 and ESP32 have plenty of memory so commenting out fonts is not
// normally necessary. If all fonts are loaded the extra FLASH space required is
// about 17Kbytes. To save FLASH space only enable the fonts you need!

#define LOAD_GLCD   // Font 1. Original Adafruit 8 pixel font needs ~1820 bytes in FLASH
#define LOAD_FONT2  // Font 2. Small 16 pixel high font, needs ~3534 bytes in FLASH, 96 characters
#define LOAD_FONT4  // Font 4. Medium 26 pixel high font, needs ~5848 bytes in FLASH, 96 characters
#define LOAD_FONT6  // Font 6. Large 48 pixel high font, needs ~2666 bytes in FLASH, only characters 1234567890:-.apm
#define LOAD_FONT7  // Font 7. 7 segment 48 pixel high font, needs ~2438 bytes in FLASH, only characters 1234567890:-.
#define LOAD_FONT8  // Font 8. Large 75 pixel high font needs ~3256 bytes in FLASH, only characters 1234567890:-.
//#define LOAD_FONT8N // Font 8. Alternative to Font 8 above, slightly narrower, so 3 digits fit a 160 pixel TFT
#define LOAD_GFXFF  // FreeFonts. Include access to the 48 Adafruit_GFX free fonts FF1 to FF48 and custom fonts

// Comment out the #define below to stop the SPIFFS filing system and smooth font code being loaded
// this will save ~20kbytes of FLASH
#define SMOOTH_FONT

// ##################################################################################
//
// Section 4. Other options
//
// ##################################################################################

// For RP2040 processor and SPI displays, uncomment the following line to use the PIO interface.
//#define RP2040_PIO_SPI // Leave commented out to use standard RP2040 SPI port interface

// For RP2040 processor and 8 or 16 bit parallel displays:
// The default 8 bit parallel interface uses PIO, but the 16 bit parallel interface uses GPIO
// To use GPIO for the 8 bit interface, uncomment the next line. GPIO is about 5% faster.
//#define RP2040_PIO_INTERFACE // Leave commented out to use the PIO interface

// For ESP32 Dev board (only tested with ILI9341 display)
// The hardware SPI can be mapped to any pins

//#define TFT_MISO 19
//#define TFT_MOSI 23
//#define TFT_SCLK 18
//#define TFT_CS   15  // Chip select control pin
//#define TFT_DC    2  // Data Command control pin
//#define TFT_RST   4  // Reset pin (could connect to RST pin)
//#define TFT_RST  -1  // Set TFT_RST to -1 if display RESET is connected to ESP32 board RST

// For ESP32 Dev board (only tested with GC9A01 display)
// The hardware SPI can be mapped to any pins

//#define TFT_MOSI 15 // In some display driver board, it might be written as "SDA" and so on.
//#define TFT_SCLK 14
//#define TFT_CS   5  // Chip select control pin
//#define TFT_DC   27 // Data Command control pin
//#define TFT_RST  33 // Reset pin (could connect to Arduino RESET pin)
//#define TFT_BL   22 // LED back-light

//#define TOUCH_CS 21     // Chip select pin (T_CS) of touch screen

//#define TFT_WR 22    // Write strobe for modified Raspberry Pi TFT only

// ##################################################################################
//
// Section 5. Call up the right driver file and any options for it
//
// ##################################################################################

// For ESP32 Dev board (only tested with ILI9341 display)
// The XPT2046 requires a SPI port, and a touch controller address.
//#define XPT2046_IRQ 36
//#define XPT2046_MOSI 32
//#define XPT2046_MISO 39
//#define XPT2046_CLK 25
//#define XPT2046_CS 33

// ##################################################################################
//
// Section 6. Define the SPI frequency to be used for the TFT SPI bus
//
// ##################################################################################

#define SPI_FREQUENCY  40000000
//#define SPI_FREQUENCY  20000000
//#define SPI_FREQUENCY  27000000 // Actually sets it to 26.67MHz = 80/3

// Optional reduced SPI frequency for reading TFT
#define SPI_READ_FREQUENCY  20000000

// The XPT2046 requires a lower SPI clock rate of 2.5MHz so we define that here:
#define SPI_TOUCH_FREQUENCY  2500000

// ##################################################################################
//
// Section 7. Comment out / uncomment options below to remove or add functions
//            Default is to include all functions
//
// ##################################################################################

// Comment out the next #define if you do not want support for Unicode 16 bit Big Endian encoded text rendering
//#define SUPPORT_UTF8_UNICODE

// Comment out the next #define if you do not want the "Smooth" font extension
#define SMOOTH_FONT

// Comment out the next #define if you do not want to use DMA with ESP32 parallel interface (modes 1 and 2 only)
//#define ESP32_PARALLEL_DMA

// ESP32 processor only - comment out the next #define if you do not want to use DMA with the SPI interface (ESP32 only)
// The ESP32 DMA SPI is only supported on SPI port 1 and 2, other processors will ignore this
#define ESP32_DMA_CHANNEL 1 // ESP32 DMA channel (1 or 2) - Channel 1 is preferred as it has fewer restrictions

// Comment out the next #define if you do not want to use the slower DMA from SPI to memory and the screen does
// not support reading from the screen memory
//#define ESP32_DMA_BUFFER_SIZE 64 // 64 to 512 samples, powers of 2, default 64

// Transactions are automatically enabled by the library for an ESP32 (to use HAL mutex)
// so changing it here has no effect

// #define SUPPORT_TRANSACTIONS

#endif // USER_SETUP_H