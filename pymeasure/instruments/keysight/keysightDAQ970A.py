#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2025 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
import numpy as np
from pymeasure.instruments import Instrument, SCPIUnknownMixin
from pymeasure.instruments.validators import strict_discrete_set, strict_range
from pymeasure.instruments import VisaInstrument, MeasurementError


class KeysightDAQ970A(VisaInstrument):
    """Driver for the Keysight DAQ970A Data Acquisition System.

    Usage:
        instrument = DAQ970A("GPIB::16", timeout=5000)
        instrument.reset()
        print(instrument.identify())
        instrument.configure_channel("101", mode="VOLT:DC", rng=10, resolution=6)
        value = instrument.measure("101")
    """

    def __init__(self, resource_name, **kwargs):
        super().__init__(
            resource_name,
            "Keysight DAQ970A",
            includeSCPI=False,
            **kwargs
        )
        # Ensure proper line endings
        self.write_termination = "\n"
        self.read_termination  = "\n"
        # Reset to known state
        self.reset()

    def reset(self):
        """Resets the instrument to default settings."""
        self.write("*RST")

    def identify(self):
        """Returns the instrument identification string."""
        return self.ask("*IDN?").strip()

    def list_channels(self):
        """Returns a list of defined channel numbers."""
        # Queries the instrument for active channels
        resp = self.ask("SYST:CHAN:DEF?")
        return [ch.strip() for ch in resp.split(",") if ch.strip()]

    def configure_channel(self, channel, mode, rng=None, resolution=None):
        """Configures a single channel for measurement.

        Arguments:
            channel (str): Channel specifier, e.g. "101" or "102".
            mode (str): Measurement function, e.g. "VOLT:DC", "CURR:AC", "TEMP".
            rng (float, optional): Desired range; if None, leaves range unchanged.
            resolution (int, optional): Resolution digits; if None, leaves resolution.
        """
        # Set function
        self.write(f"CONFigure:{mode} (@{channel})")
        # Set range if given
        if rng is not None:
            self.write(f"SENS:{mode}:RANG {rng},(@{channel})")
        # Set resolution if given
        if resolution is not None:
            self.write(f"SENS:{mode}:RES {resolution},(@{channel})")

    def measure(self, channel):
        """Triggers and returns a single measurement on the given channel.

        Arguments:
            channel (str): Channel specifier, e.g. "101".
        Returns:
            float: Measured value.
        """
        resp = self.ask(f"READ? (@{channel})")
        try:
            return float(resp)
        except ValueError:
            raise MeasurementError(f"Unexpected response for channel {channel}: {resp}")

    def measure_all(self):
        """Triggers and returns measurements of all configured channels.

        Returns:
            list of float: Values in channel-order.
        """
        resp = self.ask("READ?")
        values = resp.strip().split(",")
        try:
            return [float(v) for v in values]
        except ValueError as e:
            raise MeasurementError(f"Invalid data block: {resp}") from e
        
    # ———————————————————————————————————————————————————————————————
    # Temperature (Thermocouple) Methods
    # ———————————————————————————————————————————————————————————————

    def configure_temperature_tc(self, channel, tc_type, rng=None, resolution=None):
        """Configure a channel for thermocouple temperature (e.g. type 'K', 'J')."""
        mode = "TEMP:TC"
        # Set thermocouple type
        self.write(f"CONFigure:{mode} {tc_type},(@{channel})")
        # Optionally set range and resolution
        if rng is not None:
            self.write(f"SENS:{mode}:RANG {rng},(@{channel})")
        if resolution is not None:
            self.write(f"SENS:{mode}:RES {resolution},(@{channel})")

    def measure_temperature(self, channel):
        """Return a temperature reading (in °C) from a thermocouple channel."""
        return self.measure(channel)

    # ———————————————————————————————————————————————————————————————
    # Resistance Methods
    # ———————————————————————————————————————————————————————————————

    def configure_resistance(self, channel, rng=None, resolution=None):
        """Configure a channel for 2-wire resistance measurement."""
        self.configure_channel(channel, mode="RES", rng=rng, resolution=resolution)

    def measure_resistance(self, channel):
        """Return a resistance reading (in ohms) from a channel."""
        return self.measure(channel)

    # ———————————————————————————————————————————————————————————————
    # Frequency Methods
    # ———————————————————————————————————————————————————————————————

    def configure_frequency(self, channel, rng=None, resolution=None):
        """Configure a channel for frequency measurement."""
        self.configure_channel(channel, mode="FREQ", rng=rng, resolution=resolution)

    def measure_frequency(self, channel):
        """Return a frequency reading (in Hz) from a channel."""
        return self.measure(channel)

    @property
    def autorange(self):
        """Gets or sets autoranging for DC voltage measurements."""
        resp = self.ask("SENS:VOLT:DC:RANG:AUTO?")
        return bool(int(resp))

    @autorange.setter
    def autorange(self, enable):
        state = "ON" if enable else "OFF"
        self.write(f"SENS:VOLT:DC:RANG:AUTO {state}")