import math
from math_util import *
from constants import g

class Model:
    pass


class ModelArm(Model):
    def __init__(self, mass, length, motor, bearing=None):
        self.mass = mass
        self.length = length
        self.motor = motor
        self.bearing = bearing
        self.adjust()

    def calculate(self, position, velocity, dt, output):
        result = self.motor.torque(velocity, output)
        result['torque_from_gravity'] = (-g * self.mass * math.cos(position)) * self.centre_of_mass
        torque = result['gearbox_torque'] + result['torque_from_gravity']
        bearing_friction = self.bearing.friction(self.mass) if self.bearing is not None else 0
        result['bearing_friction'] = -math.copysign(min(abs(torque), bearing_friction), velocity)
        result['torque'] = torque + result['bearing_friction']
        result['acceleration'] = result['torque'] * self.inertia
        result['velocity'] = velocity + result['acceleration'] * dt
        new_position = position + dt * (velocity + result['velocity'])/2 
        result['position'] = input_modulus(new_position, -math.pi, math.pi)
        result['position_deg'] = radians_to_degrees(result['position'] )
        result['velocity_deg'] = radians_to_degrees(result['velocity'])
        result['acceleration_deg'] = radians_to_degrees(result['acceleration']),
        return result

    def ff(self, f, setpoint):
      return (f * math.cos(setpoint))

    def set_mass(self, value):
        self.mass = value
        self.adjust()

    def set_length(self, value):
        self.length = value
        self.adjust()

    def adjust(self):
        # Assume uniform mass
        self.inertia = self.mass * self.length ** 2 / 3.0
        self.centre_of_mass = self.length * 0.5
 


    @property
    def columns(self):
        return [
            'position', 'velocity', 'acceleration', 
            'position_deg', 'velocity_deg', 'acceleration_deg', 
            'motor_torque', 'torque', 'torque_from_gravity', 'bearing_friction'] + self.motor.columns
