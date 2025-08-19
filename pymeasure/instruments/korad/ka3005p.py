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
from time import sleep

import numpy as np

from pymeasure.instruments import Instrument
from pymeasure.instruments.validators import strict_range

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class KA3005P(Instrument):
    """Represents the Korad KA3005P programmable benchtop DC power supply, and 
    provides a high-level interface for interacting with the instrument.
    
    .. code-block:: python
        from pymeasure.instruments.korad.ka3005p import KA3005P
    
        korad = KA3005P('COM5')                                 # Connect to the instrument over USB

        print(korad.id)                                         # Report instrument ID

        korad.voltage_setpoint = 20                             # Set output voltage
        korad.current_limit = 1.5                               # Set output current
        korad.disable_ocp()                                     # Disable OCP

        print("Voltage {}V".format(korad.voltage_setpoint))     # Print new voltage setting to the console
        print("Current {}A".format(korad.current_limit))        # Print new current setting to the console

        korad.enable_output()                                   # Turn on the output
        korad.voltage_setpoint = 1.5                            # Change the voltage setpoint
        korad.ramp_to_voltage(24, 10, 0.5)                      # Ramp up the voltage to 24V in 10 steps of 0.5 seconds each
        korad.ramp_to_current(3, 5, 1)                          # Ramp up the current to 3A in 5 steps of 1 second each
        korad.ocp_limit = 3.5                                   # Set the OCP current
        korad.enable_ocp()                                      # Enable OCP
        korad.disable_output()                                  # Turn the output off

        korad.shutdown()                                        # Shut the instrument down and close the VISA device             
    """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Initializer
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    def __init__(self, adapter, name="Korad KA3005P", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )

        self.disable_output()


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    idn = Instrument.measurement(
        "*IDN?",
        "Query the instrument for its VISA ID number"
    )

    voltage_setpoint = Instrument.control(
        "VSET1?", "VSET1:%05.2f",
        "Set or report the programmed output voltage.",
        validator=strict_range,
        values=[0, 30]
    )

    current_limit = Instrument.control(
        "ISET1?", "ISET1:%05.2f",
        "Set or report the programmed output current limit",
        validator=strict_range,
        values=[0, 5]
    )

    voltage = Instrument.measurement(
        "VOUT1?",
        """Measure the actual output voltage"""
    )

    current = Instrument.measurement(
        "IOUT1?",
        "Measure the actual output current"
    )

    ocp_limit = Instrument.setting(
        "OCPSET1:%05.2f",
        "Set the overcurrent protection limit.",
        validator=strict_range,
        values=[0, 5]
    )


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def reset(self):
        """Sends the RST command to reset the power supply."""
        self.write("RST")

    
    def enable_output(self):
        """Turn on the output of the power supply."""
        self.write("OUT1")


    def disable_output(self):
        """Turn off the output of the power supply."""
        self.write("OUT0")


    def enable_ocp(self):
        """Turn on overcurrent protection"""
        self.write("OCP1")


    def disable_ocp(self):
        """Turn off overcurrent protection"""
        self.write("OCP0")

    
    def ramp_to_voltage(self, target_voltage, steps=20, pause=0.2):
        """Ramps to a target voltage from the set voltage value over
        a certain number of linear steps, each separated by a pause duration.
        A minimum 200ms pause is recommended in order to give the unit sufficient 
        time to respond. Quicker steps are possible, but the behaviour of the device
        may become unpredictable.

        :param target_voltage: Target voltage in volts
        :param steps: Integer number of steps
        :param pause: Pause duration in seconds to wait between steps (min 200ms)
        """

        voltages = [round(i, 2) for i in np.linspace(self.voltage_setpoint,
                                                     target_voltage, steps)]
        for setpoint in voltages:
            self.voltage_setpoint = setpoint
            sleep(pause)


    def ramp_to_current(self, target_current, steps=20, pause=0.2):
        """Ramps to a target current from the set current value over
        a certain number of linear steps, each separated by a pause duration.
        A minimum 200ms pause is recommended in order to give the unit sufficient 
        time to respond. Quicker steps are possible, but the behaviour of the device
        may become unpredictable.

        :param target_current: Target current in amps
        :param steps: Integer number of steps
        :param pause: Pause duration in seconds to wait between steps (min 200ms)
        """

        currents = [round(i, 2) for i in np.linspace(self.current_limit,
                                                     target_current, steps)]
        for current in currents:
            self.current_limit = current
            sleep(pause)


    def shutdown(self):
        """Turns off the output and shuts the power supply down."""
        log.info("Shutting down %s." % self.name)
        self.disable_output()
        super().shutdown()
