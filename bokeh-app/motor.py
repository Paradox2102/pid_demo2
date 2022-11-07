from logging import NullHandler
from math_util import *

def rpm_to_radians_per_second(rpm):
    return rpm * 2 * math.pi / 60

class Motor:
    def __init__(self, voltage, name=None, stall_torque=None, free_speed=None):
        self.voltage = voltage
        self._name = name if name is not None else "some motor"
        self._stall_torque = stall_torque
        self._free_speed = free_speed

    def stall_torque(self, voltage):
        return self._stall_torque * voltage / self.voltage 

    def free_speed(self, voltage):
        return self._free_speed * voltage / self.voltage

    def torque(self, velocity, output):
        voltage = output * self.voltage
        stall_torque = self.stall_torque(abs(voltage))
        assert stall_torque >= 0, dict(velocity=velocity, output=output, stall_torque=stall_torque)
        free_speed = self.free_speed(abs(voltage))
        if free_speed > 0:
            torque = stall_torque * (1 - velocity * math.copysign(1.0, voltage) / free_speed)
        else:
            torque = stall_torque
        torque = math.copysign(torque, voltage)            
        return torque

    def name(self):
        return self._name


class Falcon500(Motor):
    def __init__(self):
        super().__init__(name="Vex Falcon 500", voltage=12,
            free_speed=rpm_to_radians_per_second(6380),
            stall_torque=4.69)

    # These are based on fitting a cubic polynomial to the data published here:
    # https://motors.vex.com/vexpro-motors/falcon#osf6k0e
    # Both polynomials are negative below about 0.85v.  R^2>=0.999

    def stall_torque(self, voltage):
        return max(0, -0.918 + 1.15 * voltage + -0.117 * voltage ** 2 + 5E-03 * voltage ** 3)

    def free_speed(self, voltage):
        return rpm_to_radians_per_second(max(0, -690 + 870 * voltage + -52.1 * voltage ** 2 + 2.4 * voltage ** 3))

    # TODO: Simulate brake mode
    # TODO: Calculate current, temperature


class Gearbox:
    def __init__(self, motor, ratio=1, n_motors=1):
        self.motor = motor
        self.ratio = ratio
        self.n_motors = n_motors

    def torque(self, velocity, output):
        torque = self.motor.torque(velocity * self.ratio, output)
        return torque / self.ratio * self.n_motors

    def set_ratio(self, value):
        self.ratio = value
        
    def set_n_motors(self, value):
        self.n_motors = value