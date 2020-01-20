# generator_switchover

Raspberry Pi controller for switching on a generator when a solar battery bank as a voltage &lt; 50v for an hour or until it reaches 57v.

# Parts

## Hardware

* Compute - Raspberry Pi Zero W
* uSD Card - 16GB NOOBS 3.0 
* Relay + A/D - Pimoroni Automation pHAT 
* Small Display - Adafruit Mini PiTFT 1.3"
* Break-away 0.1" 2x20-pin Strip Dual Male Header
* GPI Stacking Header for Pi

## Cables

* Display - Mini HDMI to HDMI
* Power - 2.5amp 5v micro-USB
* micro-USB USB Hub

## Libraries

* [Python Library Automation Hat](https://github.com/pimoroni/automation-hat)
* 

# Setup

Below is the setup for the system

## 0. Set computer name, user name and password

|            |            |
| ---------- | ---------- |
| Hostname   | generator  |
| User       | generator  |
| Password   | vine generator |

### Hostname

Change Hostname to `generator` with a script

```
host_name=generator
echo $host_name | tee /etc/hostname
sed -i -E 's/^127.0.1.1.*/127.0.1.1\t'"$host_name"'/' /etc/hosts
hostnamectl set-hostname $host_name
systemctl restart avahi-daemon
```

### User and Password

Change default `pi` user to `generator` and set password to `vine generator`

```
sudo usermod -l generator -d  /home/generator -m pi
usermod -c "Vine View Generator" generator
echo "vine generator" | passwd --stdin generator
```



## 1. Base OS Update

```

```

```
# First time setup
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3-pip
sudo pip3 install --upgrade setuptools
```

## 2. Setup I2C + SPI

https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c

```
sudo apt-get install -y python-smbus
sudo apt-get install -y i2c-tools
```

* Enable I2C - Run `sudo-raspi-config` then go to `5 Interfacing Options` then `I2C` then `ENABLE` then exit.
* Enable SPI - Run `sudo-raspi-config` then go to `5 Interfacing Options` then `SPI` then `ENABLE` then exit.
* Reboot - `sudo reboot`
* Test I2C - `sudo i2cdetect -y 1` - And should see some
* Test SPI - `ls -l /dev/spidev*` - And should see some



# Display
```
# https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi

# https://learn.adafruit.com/pitft-linux-python-animated-gif-player/python-setup-2

sudo pip3 install adafruit-circuitpython-rgb-display
sudo pip3 install --upgrade --force-reinstall spidev
sudo apt-get install ttf-dejavu
sudo apt-get install python3-pil
sudo apt-get install python3-numpy
```

## 3. A/D + Relay

```
sudo pip3 install automationhat

```