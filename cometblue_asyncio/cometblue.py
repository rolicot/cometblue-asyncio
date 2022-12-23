#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import platform
import asyncio
from datetime import datetime
from typing import Dict, List, Union
from uuid import UUID

from bleak import BLEDevice, BleakClient, BleakScanner
from bleak.exc import BleakError

from . import interface
from .interface import uuids, UNCHANGED_VALUE
from . import logdirect
log = logdirect.Logger(__name__)

MAC_REGEX = re.compile('(^[0-9A-F]{2}:){5}[0-9A-F]{2}$')
UUID_REGEX = re.compile('^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

class CometBlue:
    """Asynchronous adapter for Eurotronic Comet Blue (and rebranded) bluetooth TRV."""

    def __init__(self, device: Union[BLEDevice, str], pin=0, timeout=30):
        """
        :param device: Either a discovered BLEDevice or Bluetooth MAC address
            (or UUID on Darwin). If you want to connect to multiple devices at
            once, discover them with CometBlue.discover or
            CometBlue.find_multiple first.
        :param pin: PIN for the device (0 by manufacturer)
        :param timeout: discover timeout in seconds if specified as MAC/UUID.
        """
        if not isinstance(device, BLEDevice):
            if platform.system() == "Darwin":
                if not UUID_REGEX.match(device):
                    raise ValueError("device must be a valid UUID in the format "
                            "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX or "
                            "bleak.BLEDevice.")
            else:
                if not MAC_REGEX.match(device):
                    raise ValueError("device must be a valid Bluetooth Address "
                            "in the format XX:XX:XX:XX:XX:XX or "
                            "a bleak.BLEDevice.")

        if 0 > pin >= 100000000:
            raise ValueError("pin can only consist of digits. Up to 8 digits allowed.")

        self.device = device
        self.pin = interface.transform_pin(pin)
        self.timeout = timeout
        self.connected = False

    async def _read_value(self, characteristic: UUID) -> bytearray:
        """
        Reads a characteristic and provides the data as a bytearray. Disconnects afterwards.

        :param characteristic: UUID of the characteristic to read
        :return: bytearray containing the read values
        """
        return await self.client.read_gatt_char(characteristic)

    async def _write_value(self, characteristic: UUID, new_value: bytearray):
        """
        Writes a bytearray to the specified characteristic. Disconnects afterwards to apply written changes.

        :param characteristic: UUID of the characteristic to write
        :param new_value: bytearray containing the new values
        :return:
        """
        await self.client.write_gatt_char(characteristic, new_value, response=True)

    async def connect(self):
        """
        Connects to the device and transmits the PIN (necessary for most
        operations. Uses timeout unless initalized with already discovered
        BLEDevice.

        :return:
        """
        self.client = BleakClient(self.device, timeout=self.timeout)

        await self.client.connect()

        try:
            await self._write_value(uuids.PIN, self.pin)
        except:
            await self.client.disconnect()
            raise

        self.connected = True

    async def disconnect(self):
        """
        Disconnects the device.

        :return:
        """
        if self.connected:
            await self.client.disconnect()
            self.connected = False

    async def get_temperature(self) -> dict:
        """Retrieves the temperature configurations from the device.

        :return: dict of the retrieved values
        """
        value = await self._read_value(uuids.TEMPERATURE)
        return interface.transform_temperature_response(value)

    async def set_temperature(self, manualTemp=None, targetTempLow=None,
            targetTempHigh=None, tempOffset=None):
        """Sets the temperatures.
        Allowed values for updates are:
           - manualTemp: temperature for the manual mode
           - targetTempLow: lower bound for the automatic mode
           - targetTempHigh: upper bound for the automatic mode
           - tempOffset: offset for the measured temperature

        All temperatures are in 0.5°C steps
        """
        new_value = interface.transform_temperature_request(manualTemp,
                targetTempLow, targetTempHigh, tempOffset)
        await self._write_value(uuids.TEMPERATURE, new_value)

    async def get_battery(self):
        """
        Retrieves the battery level in percent from the device

        :return: battery level in percent
        """
        return (await self._read_value(uuids.BATTERY))[0]

    async def get_datetime(self) -> datetime:
        """
        Retrieve the current set date and time of the device - used for schedules

        :return: the retrieved datetime
        """
        result = await self._read_value(uuids.DATETIME)
        return interface.transform_datetime_response(result)

    async def set_datetime(self, date=None):
        """
        Sets the date and time of the device - used for schedules

        :param date: a datetime object, defaults to now
        """
        new_value = interface.transform_datetime_request(
                datetime.now() if date is None else date)
        await self._write_value(uuids.DATETIME, new_value)

    async def get_weekday(self, weekday) -> dict:
        """
        Retrieves the start and end times of all programed heating periods for the given day.

        :param weekday: weekday (0=Monday, 6=Sunday)
        :return: list containing datetime.time or None for each:
            start1, end1, start2, end2, start3, end3, start4, end4
        """
        uuid = uuids.WEEKDAYS[weekday]
        value = await self._read_value(uuid)
        return interface.transform_weekday_response(value)

    async def set_weekday(self, weekday, start1=None, end1=None, start2=None,
            end2=None, start3=None, end3=None, start4=None, end4=None):
        """
        Sets the start and end times for programed heating periods for the given day.

        :param weekday: ISO weekday (0=Monday, 6=Sunday) to set
        :param start1: datetime.time or None
        :param end1: datetime.time or None
        """

        new_value = interface.transform_weekday_request((start1, end1, start2,
        end2, start3, end3, start4, end4))
        await self._write_value(uuids.WEEKDAYS[weekday], new_value)

    async def get_holiday(self, number: int) -> dict:
        """
        Retrieves the configured holiday 0-7.

        :param number: the number of the holiday season (0-7).
        :return: dict { start: datetime, end: datetime, temperature: float }
        """
        values = await self._read_value(uuids.HOLIDAYS[number])
        return interface.transform_holiday_response(values)

    async def reset_holiday(self, number: int):
        """
        Resets the configured holiday 0-7.

        :param number: the number of the holiday season (0-7).
        """
        await self._write_value(uuids.HOLIDAYS[number], interface.NO_HOLIDAY)

    async def set_holiday(self, number: int, start, end, temperature):
        """
        Sets the configured holiday 0-7.

        :param number: the number of the holiday season (0-7).
        :param values: start: datetime, end: datetime, temperature: float (0.5 degree steps)
        """
        new_value = interface.transform_holiday_request(start, end, temperature)
        await self._write_value(uuids.HOLIDAYS[number], new_value)

    async def get_manual_mode(self) -> bool:
        """
        Retrieves if manual mode is enabled
        :return: True - if manual mode is enabled, False if not
        """
        mode = await self._read_value(uuids.SETTINGS)
        return bool(mode[0] & 0x01)

    async def set_manual_mode(self, value: bool):
        """
        Enables/Disables the manual mode.

        :param value: True - if manual mode should be enabled, False if not
        :return:
        """
        mode = bytearray(3)
        if value:
            mode[0] = 0x01

        mode[1] = interface.UNCHANGED_VALUE
        mode[2] = interface.UNCHANGED_VALUE
        await self._write_value(uuids.SETTINGS, mode)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    @classmethod
    async def discover(cls, timeout=30) -> List[BLEDevice]:
        """
        Discovers available CometBlue devices.

        :param timeout: Duration of Bluetooth scan.
        :return: List of CometBlue BLEDevices.
        """
        devices = await BleakScanner.discover(timeout, return_adv=True)
        return [d for d, adv in devices.values() 
                if interface.SERVICE in adv.service_uuids]

    @classmethod
    async def find_multiple(cls, addresses, timeout=30) -> List[BLEDevice]:
        """
        Finds multiple requested CometBlue devices by their addresses.

        :param addresses: List of requested addresses.
        :param timeout: Duration of Bluetooth scan.
        :return: List of CometBlue BLEDevices.
        """
        found_devs = [None] * len(addresses)
        idx = {a.upper(): i for i, a in enumerate(addresses)}
        stop_event = asyncio.Event()

        def callback(device, advertising_data):
            try:
                found_devs[idx.pop(device.address.upper())] = device
            except KeyError:
                return
            if not idx:
                stop_event.set()

        try:
            async with BleakScanner(callback) as scanner:
                await asyncio.wait_for(stop_event.wait(), timeout)
        except asyncio.TimeoutError:
            log.debug_('Some devices were not found:', *idx.keys())

        return found_devs


