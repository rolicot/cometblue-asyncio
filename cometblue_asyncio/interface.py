#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from struct import Struct
from uuid import UUID
from datetime import datetime, time

from . import logdirect
log = logdirect.Logger(__name__)

SERVICE = "47e9ee00-47e9-11e4-8939-164230d1df67"
UNCHANGED_VALUE = 0x80
UNCHANGED_TEMP = -128
NO_TIME = 0xFF
NO_HOLIDAY = b'\x80'*9

class uuids:
    DATETIME = UUID("47e9ee01-47e9-11e4-8939-164230d1df67")

    WEEKDAYS = [
        UUID("47e9ee10-47e9-11e4-8939-164230d1df67"), #Monday
        UUID("47e9ee11-47e9-11e4-8939-164230d1df67"), #Tuesday
        UUID("47e9ee12-47e9-11e4-8939-164230d1df67"), #Wednesday
        UUID("47e9ee13-47e9-11e4-8939-164230d1df67"), #Thursday
        UUID("47e9ee14-47e9-11e4-8939-164230d1df67"), #Friday
        UUID("47e9ee15-47e9-11e4-8939-164230d1df67"), #Saturday
        UUID("47e9ee16-47e9-11e4-8939-164230d1df67"), #Sunday
        ]

    HOLIDAYS = [
        UUID("47e9ee20-47e9-11e4-8939-164230d1df67"),
        UUID("47e9ee21-47e9-11e4-8939-164230d1df67"),
        UUID("47e9ee22-47e9-11e4-8939-164230d1df67"),
        UUID("47e9ee23-47e9-11e4-8939-164230d1df67"),
        UUID("47e9ee24-47e9-11e4-8939-164230d1df67"),
        UUID("47e9ee25-47e9-11e4-8939-164230d1df67"),
        UUID("47e9ee26-47e9-11e4-8939-164230d1df67"),
        UUID("47e9ee27-47e9-11e4-8939-164230d1df67"),
        ]

    SETTINGS = UUID("47e9ee2a-47e9-11e4-8939-164230d1df67")
    TEMPERATURE = UUID("47e9ee2b-47e9-11e4-8939-164230d1df67")
    BATTERY = UUID("47e9ee2c-47e9-11e4-8939-164230d1df67")
    UNKNOWN2 = UUID("47e9ee2d-47e9-11e4-8939-164230d1df67")
    UNKNOWN3 = UUID("47e9ee2e-47e9-11e4-8939-164230d1df67")
    PIN = UUID("47e9ee30-47e9-11e4-8939-164230d1df67")

struct_temps = Struct('<5b2B')

class CometBlueResponseValues:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def transform_pin(pin: int):
    """
    Transforms the pin a bytearray required by the Comet Blue device.

    :param pin: the pin to use
    :return: bytearray representing the pin
    """
    return pin.to_bytes(4, 'little', signed=False)

def int_to_time(value):
    """
    Transforms a Comet Blue time representation to datetime.time

    :param value:
    :return:
    """
    if value == NO_TIME:
        return None
    h, m = divmod(value, 6)
    return time(h, m*10)

def time_to_int(value):
    """
    Transforms datetime.time to the Comet Blue byte representation.

    :param value: datetime.time
    :returns int: the Comet Blue representation of the given time
    :rtype: int
    """
    if value is None:
        return NO_TIME
    return value.hour * 6 + value.minute / 10

def transform_temperature_response(value: bytearray) -> dict:
    """
    Transforms a temperature response to a dictionary containing the values.

    :param value: bytearray retrieved from the device
    :return: dict containing the values
    """
    v = struct_temps.unpack(value)
    result = CometBlueResponseValues(
        currentTemp       = v[0] / 2.,
        manualTemp        = v[1] / 2.,
        targetTempLow     = v[2] / 2.,
        targetTempHigh    = v[3] / 2.,
        tempOffset        = v[4] / 2.,
        windowOpen        = v[5] == 0xF0,
        windowOpenMinutes = v[6],
        )

    return result

temperature_to_int = lambda temp: (
        UNCHANGED_TEMP if temp is None else int(temp*2))

def transform_temperature_request(manualTemp=None, targetTempLow=None,
            targetTempHigh=None, tempOffset=None) -> bytearray:
    """
    Transforms a temperatures to a bytearray to be transferred to the device.
    """
    new_value = (
        UNCHANGED_TEMP,
        temperature_to_int(manualTemp),
        temperature_to_int(targetTempLow),
        temperature_to_int(targetTempHigh),
        temperature_to_int(tempOffset),
        UNCHANGED_VALUE,
        UNCHANGED_VALUE,
        )
    return struct_temps.pack(new_value)

def transform_datetime_response(value: bytearray) -> datetime:
    """
    Transforms a date response to a datetime object.

    :param value: the retrieved bytearray
    :return: the transformed datetime
    """
    minute = value[0]
    hour = value[1]
    day = value[2]
    month = value[3]
    year = value[4] + 2000
    dt = datetime(year, month, day, hour, minute)
    return dt

def transform_datetime_request(value: datetime) -> bytearray:
    """
    Transforms a datetime object to a bytearray to be transferred to the device.

    :param value: the datetime to be transferred
    :return: bytearray representation of the datetime
    """
    new_value = bytearray(5)
    new_value[0] = value.minute
    new_value[1] = value.hour
    new_value[2] = value.day
    new_value[3] = value.month
    new_value[4] = value.year % 100
    return new_value

def transform_weekday_response(value: bytearray) -> dict:
    """
    Transforms a weekday response to a dictionary containing all four start and end times.

    :param value: bytearray retrieved from the device
    :return: dict containing start1-4 and end1-4 times
    """
    return list(map(int_to_time, value))

def transform_weekday_request(times) -> bytearray:
    """
    Transforms a list containing datetime.time or None for each:
        start1, end1, start2, end2, start3, end3, start4, end4
    to a bytearray used by the device.

    """
    new_value = bytearray(8)
    for i, t in enumerate(times):
        new_value[i] = time_to_int(t)

    return new_value

def transform_holiday_response(values: bytearray):
    try:
        start = datetime(values[3] + 2000, values[2], values[1], values[0])
        end = datetime(values[7] + 2000, values[6], values[5], values[4])
    except ValueError:
        log.debug_('returned holiday:', values)
        return None

    temperature = values[8] / 2.

    return (start, end, temperature)

def transform_holiday_request(start, end, temp) -> bytearray:
    assert start != end and 29 > temperature >= 8
    new_value = bytearray(9)
    new_value[0] = start.hour
    new_value[1] = start.day
    new_value[2] = start.month
    new_value[3] = start.year % 100
    new_value[4] = end.hour
    new_value[5] = end.day
    new_value[6] = end.month
    new_value[7] = end.year % 100
    new_value[8] = int(temp*2)

    return new_value
