from math_util import clamp
from time import time
from motor import Motor, Gearbox
from pid import PID
from model import ModelArm

class Process:
    def __init__(self, f=0):
        self.last_time = time()
        self.start = time()
        motor = Motor(inertia=0.5, torque=12.0)
        motor = Gearbox(motor, 20)
        self.model = ModelArm(mass=0.1, length=1.0, motor=motor) 
        self.f = f
        self.output = 0
        self.pid = PID()
        self.pid.enable_continuous_input(-180, 180)
        self.voltage = 12
        self.reset()

    def update(self):
        now = time()
        dt = now - self.last_time
        self.last_time = now
        (self.position, self.velocity, acceleration) = self.model.calculate(position=self.position, velocity=self.velocity, dt=dt, output=self.output)
        result = self.pid.calculate(measurement=self.position, dt=dt)        
        # voltage and self.output are clamped, other outputs are not
        result['f_output'] = self.model.ff(self.f, self.pid.setpoint)        
        result['output'] = result['output'] + result['f_output']
        self.output = clamp(result['output'], -1, 1)
        result['voltage'] = self.output * self.voltage
        result['p_voltage'] = clamp(result['p_output'], -1, 1) * self.voltage
        result['i_voltage'] = clamp(result['i_output'], -1, 1) * self.voltage
        result['d_voltage'] = clamp(result['d_output'], -1, 1) * self.voltage
        result['f_voltage'] = clamp(result['f_output'], -1, 1) * self.voltage
        result['position'] = self.position
        result['velocity'] = self.velocity
        result['acceleration'] = acceleration
        result['ts'] = now - self.start
        assert set(result.keys()) == set(self.columns), (sorted(result.keys()), sorted(self.columns))
        return result

    def reset(self):
        self.position = -90
        self.velocity = 0
        self.pid.reset()
        self.pid.calculate(measurement=self.position, dt=None)

    def set_f(self, value):
        self.f = value

    @property
    def columns(self):
        return ['voltage', 'position', 'velocity', 'acceleration', 'ts', 
            'f_voltage', 'f_output', 'p_voltage', 'i_voltage', 
            'd_voltage'] + self.pid.columns