from math_util import *

class Motor:
    def __init__(self, inertia, torque, deadband=0.1):
        self.inertia = inertia
        self.deadband = deadband
        self.torque = torque
        
    def calculate(self, velocity, output):
        torque_from_motor = apply_deadband(output, self.deadband) * self.torque
        torque_from_friction = - 0.3 * velocity - 0.1 * (1 if velocity > 0 else -1)
        torque = torque_from_motor + torque_from_friction
        return torque
        

class Gearbox:
    def __init__(self, motor, ratio):
        self.motor = motor
        self.ratio = ratio

    def calculate(self, velocity, output):
        torque = self.motor.calculate(velocity / self.ratio, output)
        return torque * self.ratio

    def set_ratio(self, value):
        self.ratio = value