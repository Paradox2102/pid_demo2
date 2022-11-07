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
        # Assume uniform mass
        self.inertia = mass * length ** 2 / 3.0
        self.centre_of_mass = length * 0.5
        
    def calculate(self, position, velocity, dt, output):
        motor_torque = self.motor.torque(velocity, output)
        torque_from_gravity = (-g * self.mass * math.cos(position)) * self.centre_of_mass
        torque = motor_torque + torque_from_gravity
        acceleration = torque * self.inertia  
        new_velocity = (velocity + acceleration * dt)
        new_position  = position + dt * (velocity + new_velocity)/2 
        new_position = input_modulus(new_position, -math.pi, math.pi)
        return dict(
            position=new_position, 
            velocity=new_velocity, 
            acceleration=acceleration,
            position_deg=radians_to_degrees(new_position), 
            velocity_deg=radians_to_degrees(new_velocity), 
            acceleration_deg=radians_to_degrees(acceleration),
            torque=torque,
            motor_torque=motor_torque,
            torque_from_gravity=torque_from_gravity)

    def ff(self, f, setpoint):
      return (f * math.cos(setpoint))


    @property
    def columns(self):
        return [
            'position', 'velocity', 'acceleration', 
            'position_deg', 'velocity_deg', 'acceleration_deg', 
            'motor_torque', 'torque', 'torque_from_gravity']
