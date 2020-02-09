#!/usr/bin/env python3


import sys
import os
import json
from time import time, sleep
import logging
import platform
import threading
from scripts import generator_loggers

is_simulator = "Darwin" in platform.platform()
params = {}

if not is_simulator:
    import automationhat

def load_params( ):
    '''
    Loads all the parameters for the system from a json
    file so we can easily reference them and update without 
    changing code. It will be reloaded by the code every few 
    seconds so that you can easily edit it and adjust

    '''
    with open("scripts/parameters.json") as f:
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
    with open("scripts/simulator.json") as f:
        return json.load(f)


def get_battery_voltage( ):
    '''
    Returns the voltage of the batteries by reading the analog
    input which is on a voltage divider.

    '''
    global params

    voltage =  load_simulator()["analog.one"] if is_simulator else automationhat.analog.one.read()

    return voltage*params["voltage_divider"]


def get_ac_current_amps( ):
    '''
    Returns the current at this time based on the current
    sensor. As this is 60 hz, it should be sampled at a 
    stable interval.

    '''
    global params

    amps = load_simulator()["analog.two"] if is_simulator else automationhat.analog.two.read()

    return amps*params["ac_current_divider"]


def set_generator( state ):
    '''

    '''

    if state is "on":
        automationhat.relay.one.on()
    elif state is "off":
        automationhat.relay.one.off()


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
        if get_battery_voltage() < params["low_charge_voltage"]:

            # If we have a low voltage, set the start time
            # to now if we haven't started
            if time_of_low_voltage is None:
                time_of_low_voltage = time()

            elapsed_low_voltage_time = time() - time_of_low_voltage

            if elapsed_low_voltage_time > params["low_voltage_secs_before_generator"]:
                time_of_low_voltage = None
                charge_batteries_with_generator( )
        else:
            time_of_low_voltage = None


def charge_batteries_with_generator( ):
    '''
    This is triggered if there is a low voltage on the batteries
    for more than a few minutes and will charge it up to the maximum
    57.6 volts and then sit there for a period of time.
    '''

    logger.info("Starting to charge because voltage is low ")
    start_time = time()
    elapsed = 0

    try:

        set_generator("on")

        ######################################################################
        # STEP 1 - BRING TO 57.6 V. THIS MAY TAKE AN HOUR?
        ######################################################################

        while elapsed < params["maximum_time_charging_to_full_voltage"]:
            elapsed = time() - start_time()
            if get_battery_voltage() > params["full_charge_voltage"]:
                logger.info("Full voltage during charging after " + str(elapsed/60) + " minutes.")
                break
        else:
            logger.error("Did not get to full voltage in maximum time: " + str(get_battery_voltage()) + " after " + str(elapsed))

        ######################################################################
        # STEP 2 - CHARGE AT THAT VOLTAGE FOR A PERIOD OF TIME
        ######################################################################

        start_trickle_charge = time()
        elapsed_trickle_charge = 0

        while elapsed_trickle_charge < params["trickle_charge_time"]:
            sleep(60)
            logger.debug("    " + str(round(elapsed/60)) + " min. Voltage: " + str(round(get_battery_voltage(), 1)))
        
        logger.info("CHARGE COMPLETE AFTER " + str(charge_minutes) + " minutes.")
    except Exception as e:
        logger.exception("Exception while charging batteries with generator")
    finally:
        logger.info("Ended charging after " + str(elapsed/60) + " minutes.")
        set_generator("off")

def threaded_display( ):

    while True:
        sleep(10)
        logger.info("Voltage: " + str(round(get_battery_voltage(),1)) + " volts. Current: " + str(round(get_ac_current_amps(),2)) + " amps.")


if __name__ == "__main__":
    
    logger = logging.getLogger("generator")

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

    while True:
        sleep(1)


