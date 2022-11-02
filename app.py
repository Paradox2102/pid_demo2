import math

import pandas as pd
from time import time, sleep
from typing import NamedTuple
import threading

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.io import show, output_notebook
from bokeh.plotting import figure, curdoc
from bokeh.driving import linear
from bokeh.models.ranges import DataRange1d, Range1d

class Config(NamedTuple):
    p: float
    i: float
    d: float
    izone: float
    f: float
    setpoint: float


class PID:
    def __init__(self):
        self.last_err = None
        self.err_acc = 0
        self.continuous = False
        
    def enable_continuous_input(self, minimum_input, maximum_input):
        self.continuous = True
        self.minimum_input = minimum_input
        self.maximum_input = maximum_input
        self.error_bound = (maximum_input - minimum_input) / 2.0
        
    def calculate(self, measurement, config:Config, dt):
        err = self._calculate_error(measurement, config.setpoint)
        p_output = config.p * err
        if dt is not None:
            assert self.last_err is not None, f"dt={dt}"
            d_err = (err - self.last_err) / dt
        else:
            d_err = 0
        self.last_err = err

        d_output = config.d * d_err
        
        if abs(err) < config.izone and dt is not None:
            self.err_acc += err * dt
        else:
            self.err_acc = 0
        i_output = config.i * self.err_acc
        return p_output + d_output + i_output
    
    def _calculate_error(self, measurement, setpoint):
        if self.continuous:
            return input_modulus(setpoint - measurement, -self.error_bound, +self.error_bound)
        else:
            return setpoint - measurement

# https://first.wpi.edu/wpilib/allwpilib/docs/release/java/src-html/edu/wpi/first/math/MathUtil.html

def input_modulus(input, minimum, maximum):
    modulus = maximum - minimum
    num_max = int((input - minimum) / modulus)
    input -= num_max * modulus
    num_min = int((input - maximum) / modulus)
    input -= num_min * modulus
    return input


def clamp(value, low, high):
    return max(low, min(value, high))


def apply_deadband(value, deadband):
    if abs(value) > deadband:
        if value > 0.0:
            return (value-deadband) / (1.0 - deadband)
        else:
            return (value + deadband) / (1.0 - deadband)
    else:
        return 0.0


def ff_arm(f, setpoint):
  return (f * math.cos(setpoint * math.pi / 180))


class Motor:
    def __init__(self, inertia, torque, deadband=0.1):
        self.inertia = inertia
        self.deadband = deadband
        self.torque = torque
        
    def calculate(self, velocity, output):
        torque_from_motor = apply_deadband(output, self.deadband) * self.torque
        torque_from_friction = - 0.1 * velocity - 0.1 * (1 if velocity > 0 else -1)
        torque = torque_from_motor + torque_from_friction
        return torque
        
        
g = 10


class Model:
    pass


class ModelArm(Model):
    def __init__(self, mass, length, motor, initial_position=0, initial_velocity=0):
        self.mass = mass
        self.length = length
        self.motor = motor
        self.position = initial_position
        self.velocity = initial_velocity
        self.inertia = mass * length ** 2 / 3.0
        
    def calculate(self, position, velocity, dt, output):
        motor_torque = self.motor.calculate(velocity, output)
        torque_from_gravity = (-g * self.mass * math.cos(math.pi * position / 180)) * (self.length / 2.0)
        acceleration = (motor_torque + torque_from_gravity) * self.inertia  
        new_velocity = (velocity + acceleration * dt)
        new_position  = position + dt * (velocity + new_velocity)/2 
        new_position = input_modulus(new_position, -180, 180)
        return (new_position, new_velocity)


class Process:
    def __init__(self, config):
        self.last_time = time()
        self.start = time()
        motor = Motor(inertia=0.5, torque=12.0)
        self.position = -90
        self.velocity = 0
        self.model = ModelArm(mass=1.0, length=1.0, motor=motor, initial_position=self.position, initial_velocity=self.velocity) 
        self.pid = PID()
        self.pid.calculate(measurement=self.position, config=config, dt=None)
        self.ff = ff_arm

    def update(self, config):
        now = time()
        dt = now - self.last_time
        self.last_time = now
        output_feedback = self.pid.calculate(measurement=self.position, config=config, dt=dt)
        output_feedforward = self.ff(config.f, config.setpoint)
        output = output_feedback + output_feedforward
        (self.position, self.velocity) = self.model.calculate(position=self.position, velocity=self.velocity, dt=dt, output=output)
        return (now-self.start, self.position, self.velocity, output)


def bkapp(doc):
    source = ColumnDataSource(dict(
        ts=[],
        setpoint=[],
        position=[],
        velocity=[],
        voltage=[],
        p=[],
        i=[],
        d=[],
        f=[],
    ))

    frequency = 20.

    p1 = figure(sizing_mode='stretch_width', height=200, title="Position & Setpoint")
    p1.line(x='ts', y='setpoint', color="firebrick", line_width=2, source=source)
    p1.line(x='ts', y='position', color="navy", line_width=2, source=source)

    p2 = figure(sizing_mode='stretch_width', height=200, title="Velocity")
    p2.line(x='ts', y='velocity', color="green", line_width=2, source=source)

    p4 = figure(sizing_mode='stretch_width', height=200, title="Voltage")
    p4.line(x='ts', y='voltage', color="cyan", line_width=2, source=source)

    p5 = figure(sizing_mode='stretch_width', height=200, title="PIDF")
    p5.line(x='ts', y='p', color="magenta", line_width=2, source=source)
    p5.line(x='ts', y='i', color="yellow", line_width=2, source=source)
    p5.line(x='ts', y='d', color="turquoise", line_width=2, source=source)
    p5.line(x='ts', y='f', color="limegreen", line_width=2, source=source)

    def draw_animation(p, setpoint, position):
        p.renderers = []
        setpoint_rad = setpoint * math.pi / 180
        position_rad = position * math.pi / 180
        p.segment(0, 0, 0, -1, color="black")
        p.segment(0, 0, math.cos(setpoint_rad), math.sin(setpoint_rad), color="firebrick")
        p.segment(0, 0, math.cos(position_rad), math.sin(position_rad), color="navy")

    p3 = figure(width=250, height=200, x_range=Range1d(-1, 1), y_range=Range1d(-1, 1))
    draw_animation(p3, 0, -90)

    p_widget = Slider(start=0., end=0.1, value=0., step=0.001, title="p", sizing_mode="stretch_width", format='0.000')
    f_widget = Slider(start=0., end=1, value=0., step=0.01, title="f", sizing_mode="stretch_width")
    i_widget = Slider(start=0., end=1, value=0., step=0.01, title="i", sizing_mode="stretch_width")
    d_widget = Slider(start=0., end=1, value=0., step=0.01, title="d", sizing_mode="stretch_width")
    izone_widget = Slider(start=0., end=90, value=20., step=5, title="izone", sizing_mode="stretch_width")
    setpoint_widget = Slider(start=-180., end=180, value=0., title="setpoint", sizing_mode="stretch_width")
    
    def get_config():
        return Config(
            p=p_widget.value,
            f=f_widget.value,
            i=i_widget.value,
            d=d_widget.value,
            izone=izone_widget.value,
            setpoint=setpoint_widget.value,
        )
                
    process = Process(get_config())

    @linear()
    def update(step):
        config = get_config()
        (ts, position, velocity, output) = process.update(config)
        new_data = dict(
            ts=[ts],
            position=[position],
            velocity=[velocity],
            setpoint=[config.setpoint],
            voltage=[output*12],
            p=[config.p],
            i=[config.i],
            d=[config.d],
            f=[config.f],
        )
        draw_animation(p3, config.setpoint, position)
        source.stream(new_data, frequency*30)
        

    doc.add_root(column(f_widget, p_widget, i_widget, izone_widget, d_widget, setpoint_widget, p1, p2, p3, p4, p5, sizing_mode="stretch_both"))

    # Add a periodic callback to be run every 500 milliseconds
    doc.add_periodic_callback(update, 1.0 / frequency)
    doc.title = "PID demo"

bkapp(curdoc())
