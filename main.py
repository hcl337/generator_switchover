#!/usr/bin/env python3


import sys
import os
import json
from time import time, sleep
import logging
import platform
import threading
import atexit

from scripts import generator_loggers

logger = logging.getLogger("generator")

is_simulator = "Darwin" in platform.platform() or "mac" in platform.platform()

if not is_simulator:
    from scripts import display

is_enabled = True
is_generator_on = False
message = "<>"
params = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


if not is_simulator:
    logger.info("Running on Raspberry Pi, not simulator")
    import automationhat

def load_params( ):
    '''
    Loads all the parameters for the system from a json
    file so we can easily reference them and update without 
    changing code. It will be reloaded by the code every few 
    seconds so that you can easily edit it and adjust

    '''
    with open(BASE_DIR + "/scripts/parameters.json") as f:
        params = json.load(f)

    params["utc_load_time"] = time()

    return params


def load_simulator( ):
    '''
    When we are not on a raspberry pi and hooked up,
    then this will provide us with the values for the 
    automationhat so we can change variables, save
    the file and test things out.

    '''
    with open(BASE_DIR + "/scripts/simulator.json") as f:
        return json.load(f)


def get_battery_voltage( ):
    '''
    Returns the voltage of the batteries by reading the analog
    input which is on a voltage divider.

    '''
    global params


    voltage =  load_simulator()["analog.one"] if is_simulator else automationhat.analog.one.read()
    
    return voltage*params["voltage_multiplier"] + params["voltage_offset"]


def get_ac_current_amps( ):
    '''
    Returns the current at this time based on the current
    sensor. As this is 60 hz, it should be sampled at a 
    stable interval.

    '''
    global params

    amps = load_simulator()["analog.two"] if is_simulator else automationhat.analog.two.read()

    return  (amps*amps*params["ac_current_multiplier_2"] + amps*params["ac_current_multiplier"] + params["ac_current_offset"])*params["ac_current_divider"]


def set_generator( state ):
    '''

    '''
    global is_generator_on

    if not is_simulator:
        if state == "on":
            automationhat.relay.one.on()
            is_generator_on = True
            logger.info("Generator on")
        elif state == "off":
            automationhat.relay.one.off()
            is_generator_on = False
            logger.info("Generator on")


def is_voltage_low( ):
    '''

    '''

    return get_battery_voltage() <= params["low_charge_voltage"]


def is_voltage_full( ):
    '''

    '''
    return get_battery_voltage() > params["full_charge_voltage"]


def threaded_measure_current( ):
    '''
    Loop in the background, measuring the current 20x per second
    and creating a 
    '''

    last_time = time()

    while True:
        # Sleep for 1/20th of a second so we are sampling pretty fast
        # and in line with the 60 hz signal

        elapsed = time() - last_time

        charge = get_ac_current_amps( ) * elapsed
        # TODO - Is this right - charge * voltage? And should it be 120?
        power = charge * 120.0

        last_time = time()

        sleep(0.05)


def threaded_charge_batteries( ):
    '''
    In this thread, loop, deciding if we should charge the 
    batteries by checking if it has been more than N seconds
    with low voltage in a row and, if so, triggering a charge
    '''

    time_of_low_voltage = None

    while True:

        sleep(10)

        if not is_enabled:
            continue

        if get_battery_voltage() < params["low_charge_voltage"]:

            # If we have a low voltage, set the start time
            # to now if we haven't started
            if time_of_low_voltage is None:
                logger.info("Voltage is below minimum. Starting countdown")
                time_of_low_voltage = time()

            elapsed_low_voltage_time = time() - time_of_low_voltage

            if elapsed_low_voltage_time > params["low_voltage_secs_before_generator"]:
                time_of_low_voltage = None
                charge_batteries_with_generator( )
                sleep(3600*5) # Don't try again for a few hours
        elif time_of_low_voltage is not None:
            time_of_low_voltage = None
            logger.info("Voltage is above minimum again. Canceling countdown")
 
def threaded_log_data( ):
    """
    Write to a CSV file at a standard interval except when the generator starts, where
    we want to start writing at a faster rate to see what is going on
    """

    global is_generator_on, is_enabled

    was_generator_on = False
    time_generator_started = 0
    time_of_last_write = 0
    write_interval = 60

    try:
        with open("./data.csv", "a+") as file:
            sleep(1)
            while True:

                if is_generator_on and not was_generator_on:
                    time_generator_started = time()
                    was_generator_on = True

                if not is_generator_on:
                    was_generator_on = False

                # When the generator starts up, we want to have high resolution
                # data to see how it starts, so let it jump
                if time() - time_generator_started < 10:
                    write_interval = 1
                elif time() - time_generator_started < 60:
                    write_interval = 5
                elif time() - time_generator_started < 60*5:
                    write_interval = 30
                else:
                    write_interval = 60

                if time() - time_of_last_write < write_interval:
                    sleep(0.5)
                    time_of_last_write = time()

                data_str = str(time()) + ", " + str(is_enabled) + ", " + str(get_battery_voltage()) + ", " + str(get_ac_current_amps()) + ", " + str(message) + "\n"
                file.write(data_str)

    except Exception as e:
        is_enabled = False
        logger.exception("Exception in data logging thread: " + str(e))

def charge_batteries_with_generator( ):
    '''
    This is triggered if there is a low voltage on the batteries
    for more than a few minutes and will charge it up to the maximum
    57.6 volts and then sit there for a period of time.
    '''

    global is_enabled, message

    logger.info("Starting to charge because voltage is low ")
    start_time = time()
    elapsed = 0

    try:

        initial_voltage = get_battery_voltage()

        set_generator("on")

        ######################################################################
        # STEP 0 - make sure it turns on. If not, then disable it all
        ######################################################################

        sleep(10)

        charging_voltage = get_battery_voltage()

        # Voltage should go up a bunch when the generator turns on. If it doesn't, we have something wrong
        # and most likely the generator didn't actually start up because it was out of gas.
        if charging_voltage < initial_voltage + 2:
            message = "ERR: NO GEN START"
            raise Exception("Tried tot turn on generator but voltage did not increase (before: " + str(initial_voltage) + " after " + str(charging_voltage) + ") so must be out of gas.")

        ######################################################################
        # STEP 1 - BRING TO 57.6 V. THIS MAY TAKE AN HOUR?
        ######################################################################

        while elapsed < params["maximum_seconds_charging_to_full_voltage"] and is_enabled:
            sleep(10)

            if is_voltage_low():
                message = "ERR: GEN STOPPED 1"
                raise Exception("While charging, went to low voltage, so the generator is out of gas or shut off.")

            if not is_enabled:
                return

            elapsed = time() - start_time
            if get_battery_voltage() > params["full_charge_voltage"]:
                logger.info("Full voltage during charging after " + str(elapsed/60) + " minutes.")
                break
        else:
            logger.error("Did not get to full voltage in maximum time: " + str(get_battery_voltage()) + " after " + str(elapsed))
            return
            
        ######################################################################
        # STEP 2 - CHARGE AT THAT VOLTAGE FOR A PERIOD OF TIME
        ######################################################################

        start_trickle_charge = time()
        elapsed_trickle_charge = 0

        while elapsed_trickle_charge < params["trickle_charge_time"] and is_enabled:
            sleep(60)
            logger.debug("    " + str(round(elapsed/60)) + " min. Voltage: " + str(round(get_battery_voltage(), 1)))

            if is_voltage_low():
                message = "ERR: GEN STOPPED 2"
                raise Exception("While charging, went to low voltage, so the generator is out of gas or shut off.")

            if get_battery_voltage() > params["over_voltage"]:
                logger.info("    Battery hit maximum voltage so stopping charge")
                break

        logger.info("CHARGE COMPLETE AFTER " + str(charge_minutes) + " minutes.")
    except Exception as e:
        logger.exception("Exception while charging batteries with generator: " + str(e))
        is_enabled = False
    finally:

        if not is_enabled:
            logger.info("Canceled due to being disabled.")

        logger.info("Ended charging after " + str(elapsed/60) + " minutes.")
        set_generator("off")


def threaded_display( ):

    global is_enabled, message

    time_of_button = 0

    while True:
        sleep(0.1)
        #logger.info("Voltage: " + str(round(get_battery_voltage(),1)) + " volts. Current: " + str(round(get_ac_current_amps(),2)) + " amps.")

        if not is_simulator:

            if time() - time_of_button > 1:
                if display.is_button_a_pressed():
                    time_of_button = time()
                    is_enabled = not is_enabled

                    # Clear any old messages when we toggle enabling it
                    message = "< >"

            display.render(is_enabled, is_generator_on, get_battery_voltage(), get_ac_current_amps(), message)
        else:
            sleep(0.1)

            print("                                                                                ", end="\r")
            print(str(time()) + "," + str(is_enabled) + " " + str(is_generator_on) + " " + str(get_battery_voltage()) + " " + str(get_ac_current_amps()) + " " + message, end='\r')


def self_test( ):
    logger.debug("Turning on generator")
    starting_voltage = get_battery_voltage()
    set_generator("on")
    sleep(30)
    ending_voltage = get_battery_voltage()
    set_generator("off")
    logger.debug("Turning off generator")
    
    logger.info("Initial battery voltage before test: " + str(starting_voltage))
    logger.info("Ending battery voltage after test: " + str(ending_voltage))

    sleep(1)
    logger.debug("Done with self test")

    if ending_voltage - starting_voltage < 0.1:
        
        logger.info("Failed self test. Generator did not raise voltage after 30 seconds of running")
        raise
    
if __name__ == "__main__":


    try:    
        params = load_params()

        logger.info("")
        logger.info("################################################################################")
        logger.info("STARTED GENERATOR CONTROL PROGRAM")
        logger.info("################################################################################")

        logger.info("")
        logger.info("Parameters:")

        for p in params:
            logger.info("    " + p + ": " + str(params[p]))
        logger.info("")
    
        thread_current = threading.Thread(target=threaded_measure_current, name='Measure Current', daemon=True)
        thread_current.start()

        thread_charge = threading.Thread(target=threaded_charge_batteries, name='Charge Batteries', daemon=True)
        thread_charge.start()

        thread_display = threading.Thread(target=threaded_display, name='Display', daemon=True)
        thread_display.start()

        thread_data = threading.Thread(target=threaded_log_data, name='Data Logging', daemon=True)
        thread_data.start()

        try:
            self_test()
        except:
            is_enabled = False
            message = "Failed Self Test"
        else:
            message = "Passed Self Test"

        while True:
            sleep(1)

    finally:
        set_generator("off")
