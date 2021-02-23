from datetime import datetime
import digitalio
import board

from adafruit_rgb_display.rgb import color565
import adafruit_rgb_display.st7789 as st7789

from PIL import Image, ImageDraw, ImageFont

# Configuration for CS and DC pins for Raspberry Pi
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None
BAUDRATE = 64000000   # The pi can be very fast!
# Create the ST7789 display:
display = st7789.ST7789(board.SPI(), cs=cs_pin, dc=dc_pin, rst=reset_pin, baudrate=BAUDRATE,
                        rotation=90, width=240, height=240, y_offset=80)

display.fill(color565(100,0,0))

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True
buttonA = digitalio.DigitalInOut(board.D23)
buttonB = digitalio.DigitalInOut(board.D24)
buttonA.switch_to_input()
buttonB.switch_to_input()

if display.rotation % 180 == 90:
    width = display.height
    height = display.width
else:
    width = display.width
    height = display.height

FONTSIZE = 20
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', FONTSIZE)
BORDER = 20
image = Image.new('RGB', (width, height))
rotation = 270
draw = ImageDraw.Draw(image)

draw.rectangle((0,0,width-2, height-2), outline='yellow', fill='yellow')


display.image(image, rotation)

backlight.value = True

def is_button_a_pressed():
    return not buttonA.value

def is_button_b_pressed():
    return not buttonB.value

def render(is_enabled, gen_on, voltage, current, message):

    if is_button_a_pressed() or is_button_b_pressed():
        outline='white'
    else:
        outline='blue'

    if not is_enabled:
        fill='red'
    elif gen_on:
        fill='orange'
    else:
        fill='blue'

    draw.rectangle((0,0,width-2, height-2), outline=outline, fill=fill)

    draw.text((10,1*(FONTSIZE+3)), "ENABLED:", font=font, color=(255,255,255))
    draw.text((10,2*(FONTSIZE+3)), "GENERATOR:", font=font, color=(255,255,255))
    draw.text((10,3*(FONTSIZE+3)), "VOLTAGE:", font=font, color=(255,255,255))
    draw.text((10,4*(FONTSIZE+3)), "CURRENT:", font=font, color=(255,255,255))

    offset = 160
    draw.text((offset,1*(FONTSIZE+3)), str(is_enabled), font=font, color=(255,255,255))
    draw.text((offset,2*(FONTSIZE+3)), str(gen_on), font=font, color=(255,255,255))
    draw.text((offset,3*(FONTSIZE+3)), str(round(voltage,1)), font=font, color=(255,255,255))
    draw.text((offset,4*(FONTSIZE+3)), str(round(current,1)), font=font, color=(255,255,255))

    # draw an additional line of a message
    draw.text((10,5*(FONTSIZE+3)), str(message), font=font, color=(255,255,255))

    # Draw the current time so we see it change
    date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    draw.text((10,6*(FONTSIZE+3)), date, font=font, color=(255,255,255))


    display.image(image, rotation)

#render(True, False, 57.2324, -12.12213)
