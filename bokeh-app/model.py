import math
from math_util import *

g = 10


class Model:
    pass


class ModelArm(Model):
    def __init__(self, mass, length, motor):
        self.mass = mass
        self.length = length
        self.motor = motor
        self.inertia = mass * length ** 2 / 3.0
        
    def calculate(self, position, velocity, dt, output):
        motor_torque = self.motor.calculate(velocity, output)
        torque_from_gravity = (-g * self.mass * math.cos(math.pi * position / 180)) * (self.length / 2.0)
        acceleration = (motor_torque + torque_from_gravity) * self.inertia  
        new_velocity = (velocity + acceleration * dt)
        new_position  = position + dt * (velocity + new_velocity)/2 
        new_position = input_modulus(new_position, -180, 180)
        return (new_position, new_velocity, acceleration)

    def ff(self, f, setpoint):
      return (f * math.cos(setpoint * math.pi / 180))

