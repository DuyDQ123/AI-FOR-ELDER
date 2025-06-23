# Setting Up I2S Audio for Medicine Dispenser

## Hardware Connections

### 1. Raspberry Pi to PCM5102A
```
Raspberry Pi GPIO    PCM5102A Pin    Signal
GPIO12 (Pin 32)     BCK             Bit Clock
GPIO13 (Pin 33)     LRCK            Left-Right Clock
GPIO20 (Pin 38)     DIN             Data In
3.3V (Pin 1)        VCC             Power
GND (Pin 6)         GND             Ground
```

### 2. PCM5102A to PAM8403
```
PCM5102A Pin    PAM8403 Pin    Signal
LOUT            LOUT+          Left channel analog
GND             LOUT-          Left ground
ROUT            ROUT+          Right channel analog
GND             ROUT-          Right ground
```

### 3. PAM8403 to Speaker
```
PAM8403 Pin     Speaker Wire
LOUT+ or ROUT+  Red (positive)
LOUT- or ROUT-  Black (negative)
```

## Software Configuration

1. Enable I2S in `/boot/config.txt`:
```bash
sudo nano /boot/config.txt
```
Add these lines:
```
dtparam=i2s=on
dtoverlay=i2s-mmap
```

2. Install required packages:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip mpg123 sox libsox-fmt-all
pip3 install gTTS
```

3. Configure audio:
```bash
# Add I2S module
sudo modprobe snd-bcm2835

# Set default audio to I2S
sudo amixer cset numid=3 1
```

4. Test audio:
```bash
# Test with tone
play -n -c1 synth 3 sine 1000

# Test with speech
gtts-cli "Test âm thanh" --lang vi --output test.mp3
mpg123 -a hw:1,0 test.mp3
```

## Troubleshooting

1. No sound:
- Check physical connections
- Verify I2S is enabled: `lsmod | grep snd_soc_bcm2835`
- Check audio device: `aplay -l`
- Test volume: `alsamixer -c 1`

2. Poor sound quality:
- Check ground connections
- Verify power supply is stable
- Adjust PAM8403 volume

3. System hangs:
- Remove I2S module: `sudo modprobe -r snd-bcm2835`
- Re-add with different parameters: `sudo modprobe snd-bcm2835 params`