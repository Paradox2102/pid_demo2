import math

from time import time, sleep
from typing import NamedTuple
import threading

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, Button, Span
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.io import show, output_notebook
from bokeh.plotting import figure, curdoc
from bokeh.driving import linear
from bokeh.models.ranges import DataRange1d, Range1d

import cProfile
import atexit
pr = cProfile.Profile()

def start_profiling():
    pr.enable()
    print('profiling enabled')

def stop_profiling():
    #pr.print_stats()
    pr.dump_stats("pid_demo.prof")
    pr.disable()
    print('profiling disabled')

class Config(NamedTuple):
    p: float
    i: float
    d: float
    izone: float
    f: float
    setpoint: float
    ratio: int


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
        err = self._calculate_difference(config.setpoint - measurement)
        p_output = config.p * err
        if dt is not None:
            assert self.last_err is not None, f"dt={dt}"
            d_err = self._calculate_difference(err - self.last_err) / dt
        else:
            d_err = 0
        self.last_err = err

        d_output = config.d * d_err

        #print(dict(dt=dt, d_err=d_err, err=err, err_acc=self.err_acc))
        
        if abs(err) < config.izone and dt is not None and config.i > 0:
            self.err_acc += err * dt
        else:
            self.err_acc = 0
        i_output = config.i * self.err_acc
        return dict(p=p_output, d=d_output, i=i_output)
    
    def _calculate_difference(self, value):
        if self.continuous:
            return input_modulus(value, -self.error_bound, +self.error_bound)
        else:
            return value

# Following three methods are cribbed from:
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


class Process:
    def __init__(self, config):
        self.last_time = time()
        self.start = time()
        motor = Motor(inertia=0.5, torque=12.0)
        motor = Gearbox(motor, 20)
        self.reset(config)
        self.model = ModelArm(mass=0.1, length=1.0, motor=motor) 
        self.ff = ff_arm
        self.dilation = 1
        self.output = 0

    def update(self, config):
        now = time()
        dt = (now - self.last_time) * self.dilation
        self.last_time = now
        (self.position, self.velocity, acceleration) = self.model.calculate(position=self.position, velocity=self.velocity, dt=dt, output=self.output)
        output = self.pid.calculate(measurement=self.position, config=config, dt=dt)
        output['f'] = self.ff(config.f, config.setpoint)
        output['total'] = sum(output.values())
        self.output = clamp(output['total'], -1, +1)
        self.model.motor.ratio = config.ratio
        return ((now-self.start) * self.dilation, self.position, self.velocity, acceleration, output)

    def reset(self, config):
        self.position = -90
        self.velocity = 0
        self.pid = PID()
        self.pid.enable_continuous_input(-180, 180)
        self.pid.calculate(measurement=self.position, config=config, dt=None)


def get_empty_data():
    return dict(
        ts=[],
        setpoint=[],
        position=[],
        velocity=[],
        acceleration=[],
        voltage=[],
        voltage_p=[],
        voltage_i=[],
        voltage_d=[],
        voltage_f=[],
        p=[],
        i=[],
        d=[],
        f=[],
    )

data = get_empty_data()

def bkapp(doc):

    source = ColumnDataSource(get_empty_data())
    animation_source =ColumnDataSource(dict(
        setpoint_x=[],
        setpoint_y=[],
        position_x=[],
        position_y=[],
    ))
    update_frequency = 50
    window = 30
    frame_rate = 5

    p1 = figure(sizing_mode='stretch_width', height=200, title="Position & Setpoint")
    p1.renderers.extend([
        Span(location=-180, line_color='black', line_width=1),
        Span(location=-90, line_color='black', line_width=1),
        Span(location=0, line_color='black', line_width=1),
        Span(location=90, line_color='black', line_width=1),
        Span(location=180, line_color='black', line_width=1),
    ])
    p1.line(x='ts', y='setpoint', color="firebrick", line_width=2, source=source, legend_label="setpoint")
    p1.line(x='ts', y='position', color="navy", line_width=2, source=source, legend_label="position")
    p1.legend.location = "left"
    p1.toolbar.logo = None
    p1.toolbar_location = None   

    p2 = figure(sizing_mode='stretch_width', height=200, title="Velocity")
    p2.renderers.append(Span(location=0, line_color='black', line_width=1))
    p2.line(x='ts', y='velocity', color="green", line_width=2, source=source)
    p2.toolbar.logo = None
    p2.toolbar_location = None   

    p6 = figure(sizing_mode='stretch_width', height=200, title="Acceleration")
    p6.renderers.append(Span(location=0, line_color='black', line_width=1))
    p6.line(x='ts', y='acceleration', color="orange", line_width=2, source=source)
    p6.toolbar.logo = None
    p6.toolbar_location = None   

    p4 = figure(sizing_mode='stretch_width', height=200, title="Voltage")
    p4.renderers.append(Span(location=0, line_color='black', line_width=1))
    p4.line(x='ts', y='voltage', color="red", line_width=4, source=source, legend_label="total")
    p4.line(x='ts', y='voltage_p', color="magenta", line_width=2, source=source, legend_label="p")
    p4.line(x='ts', y='voltage_i', color="orange", line_width=2, source=source, legend_label="i")
    p4.line(x='ts', y='voltage_d', color="green", line_width=2, source=source, legend_label="d")
    p4.line(x='ts', y='voltage_f', color="cyan", line_width=2, source=source, legend_label="f")
    p4.legend.location = "left"
    p4.toolbar.logo = None
    p4.toolbar_location = None   

    p5 = figure(sizing_mode='stretch_width', height=200, title="PIDF")
    p5.renderers.append(Span(location=0, line_color='black', line_width=1))
    p5.line(x='ts', y='p', color="magenta", line_width=2, source=source, legend_label="p")
    p5.line(x='ts', y='i', color="yellow", line_width=2, source=source, legend_label="i")
    p5.line(x='ts', y='d', color="turquoise", line_width=2, source=source, legend_label="d")
    p5.line(x='ts', y='f', color="limegreen", line_width=2, source=source, legend_label="f")
    p5.legend.location = "left"
    p5.toolbar.logo = None
    p5.toolbar_location = None   

    p3 = figure(width=350, height=300, x_range=Range1d(-1, 1), y_range=Range1d(-1, 1))
    p3.segment(0, 0, 0, -1, color="black", line_width=1)
    p3.segment(0, 0, 'setpoint_x', 'setpoint_y', color="firebrick", line_width=2, source=animation_source)
    p3.segment(0, 0, 'position_x', 'position_y', color="navy", line_width=4, source=animation_source)
    p3.toolbar.logo = None
    p3.toolbar_location = None   

    p_widget = Slider(start=0., end=0.1, value=0., step=0.001, title="p", sizing_mode="stretch_width", format='0.000')
    f_widget = Slider(start=0., end=1, value=0., step=0.005, title="f", sizing_mode="stretch_width", format='0.000')
    i_widget = Slider(start=0., end=0.1, value=0., step=0.001, title="i", sizing_mode="stretch_width", format='0.000')
    d_widget = Slider(start=0., end=0.2, value=0., step=0.001, title="d", sizing_mode="stretch_width", format='0.000')
    izone_widget = Slider(start=0., end=90, value=20., step=5, title="izone", sizing_mode="stretch_width")
    setpoint_widget = Slider(start=-180., end=180, value=0., title="setpoint", sizing_mode="stretch_width")
    ratio_widget = Slider(start=1, end=100, value=10, title="gear ratio", sizing_mode="stretch_width")

    def get_config():
        return Config(
            p=p_widget.value,
            f=f_widget.value,
            i=i_widget.value,
            d=d_widget.value,
            izone=izone_widget.value,
            setpoint=setpoint_widget.value,
            ratio=ratio_widget.value,
        )
                
    process = Process(get_config())

    reset_button = Button(label="Reset Arm", sizing_mode="stretch_width")
    def reset():
        process.reset(get_config())
    reset_button.on_click(reset)

    reflect_button = Button(label="Reflect Setpoint", sizing_mode="stretch_width")
    def reflect():
        setpoint_widget.value = input_modulus(180 - setpoint_widget.value, -180, 180)
    reflect_button.on_click(reflect)

    #@linear()
    def update_data():
        global data
        config = get_config()
        (ts, position, velocity, acceleration, output) = process.update(config)
        data['ts'].append(ts)
        data['position'].append(position)
        data['velocity'].append(velocity)
        data['acceleration'].append(acceleration)
        data['setpoint'].append(config.setpoint)
        data['voltage'].append(clamp(output['total'], -1, 1) * 12)
        data['voltage_p'].append(clamp(output['p'], -1, 1) * 12)
        data['voltage_i'].append(clamp(output['i'], -1, 1) * 12)
        data['voltage_d'].append(clamp(output['d'], -1, 1) * 12)
        data['voltage_f'].append(clamp(output['f'], -1, 1) * 12)
        data['p'].append(config.p)
        data['i'].append(config.i)
        data['d'].append(config.d)
        data['f'].append(config.f)

    def update_animation(setpoint, position):
        setpoint_rad = setpoint * math.pi / 180
        position_rad = position * math.pi / 180
        animation_data = dict(
            setpoint_x=[math.cos(setpoint * math.pi / 180)],
            setpoint_y=[math.sin(setpoint * math.pi / 180)],
            position_x=[math.cos(position * math.pi / 180)],
            position_y=[math.sin(position * math.pi / 180)]
        )        
        animation_source.stream(animation_data, 1)

    def update_dashboard():        
        global data
        #print(len(data['ts']))
        if len(data['ts']) > 0:
            source.stream(data, int(update_frequency*window))
            update_animation(data['setpoint'][-1], data['position'][-1])
            data = get_empty_data()
        

    doc.add_root(
            column(
                row(
                    column(f_widget, p_widget, i_widget, izone_widget, d_widget, setpoint_widget, ratio_widget, sizing_mode="stretch_width"), 
                    column(p3, reset_button, reflect_button, sizing_mode="fixed"), 
                    sizing_mode="stretch_width"
                ), 
                p1, p2, p6, p4, p5, sizing_mode="stretch_both"))

    # Add a periodic callback to be run every 500 milliseconds
    doc.add_periodic_callback(update_data, 1000.0 / update_frequency)
    doc.add_periodic_callback(update_dashboard, 1000.0 / frame_rate)
    doc.title = "PID demo"

#start_profiling()
bkapp(curdoc())
#atexit.register(stop_profiling)