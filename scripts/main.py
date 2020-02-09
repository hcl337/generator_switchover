

import sys
import os
import json
import time
import logging

import generator_loggers
import sensors
import relay


logger = logging.getLogger("generator")

with open("scripts/parameters.json") as f:
    params = json.load(f)


def is_charge_low( ):
    return sensors.get_battery_voltage() <= params["low_charge_voltage"]


def is_charge_full( ):
    return sensors.get_battery_voltage() > params["full_charge_voltage"]


def charge_to_high_voltage( ):

    logger.info("Starting to charge. ")
    start_time = time.time()

    relay.turn_on( )

    # Wait at least the minimum charge time
    while time.time() - start_time < params["minimum_charge_length_seconds"]:
        time.sleep(30)
        charge_minutes = round( (time.time() - start_time) / 60, 1 )
        logger.debug("    " + str(charge_minutes) + " min. Voltage: " + str(sensors.get_battery_voltage()))
    
    # Continue charging until the maximum charge time unless we are fully charged
    while (not is_charge_full( )) and (time.time() - start_time < params["maximum_charge_length_seconds"]):
        time.sleep(30)
        charge_minutes = round( (time.time() - start_time) / 60, 1 )
        logger.debug("    " + str(charge_minutes) + " min. Voltage: " + str(sensors.get_battery_voltage()))

    logger.info("CHARGE COMPLETE AFTER " + str(charge_minutes) + " minutes.")

if __name__ == "__main__":
    
    logger.info("")
    logger.info("################################################################################")
    logger.info("STARTED GENERATOR CONTROL PROGRAM")
    logger.info("################################################################################")

    logger.info("")
    logger.info("Parameters:")
    for p in params:
        logger.info("    " + p + ": " + str(params[p]))
    logger.info("")

    while True:
        if not is_charge_low():
            sleep(10)
        else:
            charge_to_high_voltage()


