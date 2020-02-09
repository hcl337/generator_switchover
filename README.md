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

# Raspberry Pi Compute Setup

Below is the setup for the system, which will let you log in with `ssh gen@generator.local` on your local wifi network. The easiest way to do this is to first enable SSH and then log in remotely to do the rest so you can copy and paste.

## 00. Set up remote login

### SSH

Enable SSH
```
sudo systemctl enable ssh
sudo systemctl start ssh
```

Now, make sure you connect to the same wifi network and try logging in with `ssh pi@raspberrypi.local`  from your remote computer.

## 0. Set computer name, user/password and Wifi

We need to change from `pi` as the user and set a host name which makes sense. Usually this is a lot of menus so this simplifies it into a few scripts.

|            |            |
| ---------- | ---------- |
| Hostname   | generator  |
| User       | gen  |
| Password   | vine generator |

### Hostname

Change Hostname to `generator` with a script from the command line.

```
host_name=generator
sudo bash -c "echo $host_name | tee /etc/hostname"
sudo bash -c "sed -i -E 's/^127.0.1.1.*/127.0.1.1\t'\"$host_name\"'/' /etc/hosts"
hostnamectl set-hostname $host_name
```

### User and Password

Change default `pi` user to `gen` and set password to `vine generator`

```
sudo useradd gen
sudo passwd gen
# enter "vine generator"
sudo usermod -aG sudo gen
sudo nano /etc/sudoers
# Add ALL            ALL = (ALL) NOPASSWD: ALL
```

## 1. Set up Wifi

This script will set or change which wifi you connect to on boot from now on.

```
curl -o ~/wifi_setup.sh https://gist.githubusercontent.com/rjsteinert/4999792f4a7aedd532b2/raw/6f7943aea1b38ad9e7c2fb4db76015c9b4a6b306/wpa2-wifi-connect.sh

# Put in your wifi and password here
sh ~/wifi_setup.sh SSID PASSWORD
```

Install a daemon which lets you see the localhost hostname rather than hunting for the local IP address.

```
sudo apt-get install avahi-daemon

sudo cat >> /etc/avahi/services/multiple.service <<EOL
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
        <name replace-wildcards="yes">%h</name>
        <service>
                <type>_device-info._tcp</type>
                <port>0</port>
                <txt-record>model=RackMac</txt-record>
        </service>
        <service>
                <type>_ssh._tcp</type>
                <port>22</port>
        </service>
</service-group>
EOL

sudo /etc/init.d/avahi-daemon restart
```


`ssh gen@generator.local`




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