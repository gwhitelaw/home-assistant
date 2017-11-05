"""
Allows to configure a switch using Energenie Pi Mote
"""
import logging
import time

import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
import homeassistant.components.rpi_gpio as rpi_gpio
from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = []

DEPENDENCIES = ['rpi_gpio']

CONF_SOCKETS = 'sockets'

DEFAULT_INVERT_LOGIC = False

_SOCKETS_SCHEMA = vol.Schema({
    cv.positive_int: cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SOCKETS): _SOCKETS_SCHEMA
})

SOCKET_CODES = [
    [[1, 1, 1, 1], [0, 1, 1, 1]], #socket 1
    [[1, 1, 1, 0], [0, 1, 1, 0]],
    [[1, 1, 0, 1], [0, 1, 0, 1]],
    [[1, 1, 0, 0], [0, 1, 0, 0]], #socket 4
    [[1, 0, 1, 1], [0, 0, 1, 1]] #all
]
# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Raspberry PI GPIO devices."""

    switches = []
    conf_sockets = config.get(CONF_SOCKETS)
    if (conf_sockets != None):
        for socket, name in config.get(CONF_SOCKETS).items():
            _LOGGER.info("Adding Energenie Pi-mote %s on socket %s" % (name, socket))
            switches.append(EnergenieSwitch(hass, name, socket))
        add_devices(switches)
    return True


class EnergenieSwitch(SwitchDevice):
    """Representation of a Enegenie pi-mote controlled switch."""

    def __init__(self, hass, name, socket):
        """Initialize the pin."""
        self.hass = hass
        self._name = name or DEVICE_DEFAULT_NAME
        self._socket = socket
        self._on_sequence = SOCKET_CODES[socket-1][0]
        self._off_sequence = SOCKET_CODES[socket-1][1]
        self._state = True
        self.setup_multiple_ports()
        self.turn_on()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.write_to_multiple_ports(self._on_sequence)
        _LOGGER.info("Turned %s on", self.name)
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.write_to_multiple_ports(self._off_sequence)
        _LOGGER.info("Turned %s off", self.name)
        self._state = False
        self.schedule_update_ha_state()

    def setup_multiple_ports(self):
        rpi_gpio.setup_output(17) # GPIO.BOARD 11
        rpi_gpio.setup_output(27) # GPIO.BOARD 15
        rpi_gpio.setup_output(22) # GPIO.BOARD 16
        rpi_gpio.setup_output(23) # GPIO.BOARD 13
        rpi_gpio.setup_output(24) # GPIO.BOARD 18
        rpi_gpio.setup_output(25) # GPIO.BOARD 22
        rpi_gpio.write_output(25, False)
        rpi_gpio.write_output(24, False)
        rpi_gpio.write_output(17, False) # GPIO.BOARD 11
        rpi_gpio.write_output(27, False) # GPIO.BOARD 15
        rpi_gpio.write_output(22, False) # GPIO.BOARD 16
        rpi_gpio.write_output(23, False) # GPIO.BOARD 13

    def write_to_multiple_ports(self, sequence):
        """Write a value to a GPIO."""
        _LOGGER.info("Writing sequence to %s:" % (self._name))
        a, b, c, d = [bool(c) for c in sequence]
        try:
            rpi_gpio.write_output(17, d)
            _LOGGER.info("Writing %d to 17" % (d))
            rpi_gpio.write_output(22, c)
            _LOGGER.info("Writing %d to 22" % (c))
            rpi_gpio.write_output(23, b)
            _LOGGER.info("Writing %d to 23" % (b))
            rpi_gpio.write_output(27, a)
            _LOGGER.info("Writing %d to 27" % (a))
            # let it settle, encoder requires this
            time.sleep(0.1)
            # Enable the modulator
            _LOGGER.info("Enable modulator")
            rpi_gpio.write_output(25, True)
            # keep enabled for a period
            time.sleep(0.25)
            # Disable the modulator
            _LOGGER.info("Disable modulator")
            rpi_gpio.write_output(25, False)
            _LOGGER.info("True")
            return True
        except:
            return False

