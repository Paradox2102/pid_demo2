from math_util import *
from constants import g

def rpm_to_radians_per_second(rpm):
    return rpm * 2 * math.pi / 60

class Motor:
    def __init__(self, voltage, name=None, stall_torque=None, free_speed=None, stall_current=None, free_current=None):
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
        #print(dict(name=self.name, voltage=voltage, velocity=velocity, output=output, stall_torque=stall_torque, free_speed=free_speed, torque=torque))          
        return torque

    @property
    def name(self):
        return self._name

    @classmethod
    def get_by_name(cls, name):
        return cls.motors[name]


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


class CIM(Motor):
    def __init__(self):
        super().__init__(name="VEX CIM", voltage=12,
            free_speed=rpm_to_radians_per_second(5310),
            free_current=1.5,
            stall_torque=2.42,
            stall_current=133)


class MiniCIM(Motor):
    def __init__(self):
        super().__init__(name="VEX Mini CIM", voltage=12,
            free_speed=rpm_to_radians_per_second(5840),
            free_current=13,
            stall_torque=1.41,
            stall_current=89)


class BAG(Motor):
    def __init__(self):
        super().__init__(name="VEX BAG", voltage=12,
            free_speed=rpm_to_radians_per_second(13180),
            free_current=1.8,
            stall_torque=0.43,
            stall_current=53)


class VEX775Pro(Motor):
    def __init__(self):
        super().__init__(name="VEX 775 pro", voltage=12,
            free_speed=rpm_to_radians_per_second(18730),
            free_current=0.7,
            stall_torque=0.71,
            stall_current=134)


class RS775_125(Motor):
    def __init__(self):
        super().__init__(name="Andymark RS 775-125", voltage=12,
            free_speed=rpm_to_radians_per_second(5800),
            free_current=1.6,
            stall_torque=0.28,
            stall_current=18)


class AM_9015(Motor):
    def __init__(self):
        super().__init__(name="Andymark 9015", voltage=12,
            free_speed=rpm_to_radians_per_second(14270),
            free_current=3.7,
            stall_torque=0.36,
            stall_current=71)


class RS550(Motor):
    def __init__(self):
        super().__init__(name="RS550", voltage=12,
            free_speed=rpm_to_radians_per_second(19000),
            free_current=0.4,
            stall_torque=0.38,
            stall_current=84)


class BAG(Motor):
    def __init__(self):
        super().__init__(name="VEX BAG", voltage=12,
            free_speed=rpm_to_radians_per_second(13180),
            free_current=1.8,
            stall_torque=0.43,
            stall_current=53)


class NEO550(Motor):
    def __init__(self):
        super().__init__(name="REV NEO 550", voltage=12,
            free_speed=rpm_to_radians_per_second(11000),
            free_current=1.4,
            stall_torque=0.97,
            stall_current=100)



Motor.motors = { motor.name: motor for motor in 
    [ motor() for motor in [ Falcon500, CIM, MiniCIM, BAG, VEX775Pro, RS775_125, AM_9015, RS550, NEO550 ] ] }


class Gearbox:
    def __init__(self, motor, ratio=1, n_motors=1, efficiency=1.0):
        self.motor = motor
        self.ratio = ratio
        self.n_motors = n_motors
        self.efficiency = efficiency

    def torque(self, velocity, output):
        torque = self.motor.torque(velocity / self.ratio, output)
        return torque * self.ratio * self.n_motors * self.efficiency

    def set_ratio(self, value):
        self.ratio = value
        
    def set_n_motors(self, value):
        self.n_motors = value

    def set_motor(self, value):
        self.motor = value

    def set_efficiency(self, value):
        self.efficiency = value


class Bearing:
    def __init__(self, cof, radius):
        self.cof = cof
        self.radius = radius

    def friction(self, mass):
        return self.cof * self.radius * mass * g

    def set_cof(self, value):
        self.cof = value
