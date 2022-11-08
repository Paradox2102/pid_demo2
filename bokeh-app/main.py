import math
from multiprocessing.sharedctypes import Value

from time import time, sleep
from typing import NamedTuple
import threading
from collections import defaultdict
import itertools

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, Button, Span, Arrow, NormalHead, Tooltip, HelpButton, HoverTool, LinearAxis, NumericInput, Spinner, Select
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.io import show, output_notebook
from bokeh.plotting import figure, curdoc
from bokeh.driving import linear
from bokeh.models.ranges import DataRange1d, Range1d
from bokeh.core.properties import value
from bokeh.palettes import Category10_10 as palette

from process import Process
from math_util import input_modulus, radians_to_degrees, degrees_to_radians
from motor import Motor


def get_empty_data(process, controls):
    return { key: [] for key in (process.columns + list(controls.keys())) }


data = None

control_help = dict(
    p="The further away you are, the harder you push",
    i="If it's taking a long time to get there, give it a nudge",
    d="If you're getting there too quickly, slow down",
    f="Feedforward",
    izone="Only apply the 'i' term if we're this close",
    setpoint="The target, where we're trying to get to",
    ratio="The number of times the motors rotates when the arm rotates once",
)

def make_controls():
    return dict(
        p=Slider(start=0., end=0.1, value=0., step=0.001, title="p", sizing_mode="stretch_width", format='0.000'),
        f=Slider(start=0., end=1, value=0., step=0.005, title="f", sizing_mode="stretch_width", format='0.000'),
        i=Slider(start=0., end=0.1, value=0., step=0.001, title="i", sizing_mode="stretch_width", format='0.000'),
        d=Slider(start=0., end=0.2, value=0., step=0.001, title="d", sizing_mode="stretch_width", format='0.000'),
        izone=Slider(start=0., end=90, value=20., step=5, title="izone", sizing_mode="stretch_width"),
        setpoint=Slider(start=-180., end=180, value=0., title="setpoint", sizing_mode="stretch_width"),
        ratio=Spinner(low=1, high=100, value=10, title="gear ratio", sizing_mode="stretch_width"),
        mass=NumericInput(low=0.1, high=100, value=1, mode='float', title="arm mass", sizing_mode="stretch_width"),
        length=NumericInput(low=0.1, high=1, value=1, mode='float', title="arm length", sizing_mode="stretch_width"),
        cof=NumericInput(low=0, high=1, value=0.05, mode='float', title="coefficient of friction", sizing_mode="stretch_width"), 
        n_motors=Spinner(low=1, high=3, value=1, title="number of motors", sizing_mode="stretch_width"),   
        motor=Select(options=list(Motor.motors.keys()), title="motor", sizing_mode="stretch_width"),
    )

def connect_controls(process, controls):
    # P, I, and D are per-degree, and we want them to be per-radian
    controls['p'].on_change("value", lambda attr, old, new: process.pid.set_p(radians_to_degrees(new)))
    controls['i'].on_change("value", lambda attr, old, new: process.pid.set_i(radians_to_degrees(new)))
    controls['d'].on_change("value", lambda attr, old, new: process.pid.set_d(radians_to_degrees(new)))
    controls['f'].on_change("value", lambda attr, old, new: process.set_f(new))
    controls['izone'].on_change("value", lambda attr, old, new: process.pid.set_izone(degrees_to_radians(new)))
    controls['setpoint'].on_change("value", lambda attr, old, new: process.pid.set_setpoint(degrees_to_radians(new)))
    controls['ratio'].on_change("value", lambda attr, old, new: process.model.motor.set_ratio(new))
    controls['mass'].on_change("value", lambda attr, old, new: process.model.set_mass(new))
    controls['length'].on_change("value", lambda attr, old, new: process.model.set_mass(new))
    controls['cof'].on_change("value", lambda attr, old, new: process.model.bearing.set_cof(new))
    controls['n_motors'].on_change("value", lambda attr, old, new: process.model.motor.set_n_motors(new))
    controls['motor'].on_change("value", lambda attr, old, new: process.model.motor.set_motor(Motor.get_by_name(new)))
    

colors = iter(itertools.cycle(palette))

def make_line_chart(title, source, lines, spans=[0]):
    lines = [ dict(y=line) if type(line) == str else line for line in lines ]
    y_ranges = set(line['y_range_name'] for line in lines if 'y_range_name' in line)
    p = figure(sizing_mode='stretch_width', height=200, title=title)
    default = dict(x='ts', line_width=2, source=source)
    for line in lines:
        data = {**default, **line}
        if 'color' not in data:
            data['color'] = next(colors)
        p.line(**data)
    p.renderers.extend([
        Span(location=y, line_color='black', line_width=1)
        for y in spans])
    if len(lines) > 1:
        p.legend.location = "left"
    
    p.extra_y_ranges={ 
        y_range: DataRange1d(renderers=[
            renderer for line, renderer in zip(lines, p.renderers) 
            if line.get('y_range_name') == y_range], name=y_range) 
        for y_range in y_ranges 
    }
    p.y_range = DataRange1d(renderers=[
        renderer for line, renderer in zip(lines, p.renderers) 
        if 'y_range_name' not in line
    ])
    p.toolbar.logo = None
    p.toolbar_location = None   
    for y_range in y_ranges:
        if 1== len(p.extra_y_ranges[y_range].renderers):
            color = p.extra_y_ranges[y_range].renderers[0].glyph.line_color
            p.add_layout(LinearAxis(y_range_name=y_range, axis_label=y_range,
                axis_label_text_color=color,
                axis_line_color=color,
                major_label_text_color=color,
                major_tick_line_color=color,
                minor_tick_line_color=color), 
                "right")
        else:
            p.add_layout(LinearAxis(y_range_name=y_range, axis_label=y_range), "right")
    return p


def make_animation_chart(source):
    p = figure(width=300, height=300, x_range=Range1d(-1, 1), y_range=Range1d(-1, 1))
    p.axis.visible = False
    p.grid.visible = False
    p.circle(x=[0], y=[0], radius=1, color='lightgrey')
    for angle in range(-180, 180, 30):        
        angle_rad = angle * math.pi / 180
        p.segment(0, 0, math.cos(angle_rad), math.sin(angle_rad), color="grey", 
            line_width=2 if angle % 90 == 0 else 0.5)
        p.text(x=math.cos(angle_rad) * 0.9, y=math.sin(angle_rad) * 0.9,
            text = value(str(angle) + "º"),
            text_align="center",
            text_baseline="center",
            #text_font_size=7,
            angle=angle_rad - math.pi/2,
            text_color='grey',
        )
    p.add_layout(Arrow(end=NormalHead(fill_color="firebrick", size=10), 
        line_color="firebrick", x_start=0, y_start=0, x_end='setpoint_x', 
        y_end='setpoint_y', line_width=2, source=source, 
        name="setpoint"))
    p.add_layout(Arrow(end=NormalHead(fill_color="navy", size=20), 
        line_color="navy", x_start=0, y_start=0, x_end='position_x', 
        y_end='position_y', line_width=4, source=source, 
        name="position"))
    p.toolbar.logo = None
    p.toolbar_location = None   
    return p


def bkapp(doc):
    process = Process()
    controls = make_controls()
    connect_controls(process, controls)

    global data
    data = get_empty_data(process, controls)

    source = ColumnDataSource(data)
    animation_source = ColumnDataSource(dict(
        setpoint_x=[],
        setpoint_y=[],
        position_x=[],
        position_y=[],
    ))
    update_frequency = 50
    window = 30
    frame_rate = 5

    p_mechanics = make_line_chart(title="Mechanics", source=source, lines=[
        dict(y='setpoint', color="firebrick", legend_label="setpoint"),
        dict(y="position_deg", color="navy", legend_label="position"),
        dict(y="velocity_deg", legend_label="velocity", y_range_name="velocity"),
        dict(y="acceleration_deg", legend_label="acceleration", y_range_name="acceleration"),
    ], spans=[-180, -90, 0, 90, 180])

    p_voltage = make_line_chart(title="Voltage", source=source, lines=[
        dict(y='voltage', line_width=4, legend_label='total'),
        dict(y='p_voltage', legend_label='p'),
        dict(y='i_voltage', legend_label='i'),
        dict(y='d_voltage', legend_label='d'),
        dict(y='f_voltage', legend_label='f'),
    ])

    p_torque = make_line_chart(title="Torque", source=source, lines=[
        dict(y='torque', line_width=4, legend_label='Total'),
        dict(y='motor_torque', legend_label='Motor'),
        dict(y='torque_from_gravity', legend_label='Gravity'),
        dict(y='bearing_friction', legend_label='Friction'),
    ])

    p_animation = make_animation_chart(animation_source)

    reset_button = Button(label="Reset Arm", sizing_mode="stretch_width")
    reset_button.on_click(lambda: process.reset())

    reflect_button = Button(label="Reflect Setpoint", sizing_mode="stretch_width")
    def reflect():
        controls['setpoint'].value = input_modulus(180 - controls['setpoint'].value, -180, 180)
    reflect_button.on_click(reflect)

    #@linear()
    def update_data():
        global data
        for key, widget in controls.items():
            data[key].append(widget.value)

        process_result = process.update()
        for key, value in process_result.items():
            data[key].append(value)


    def update_animation(setpoint, position):
        setpoint_rad = degrees_to_radians(setpoint)
        animation_data = dict(
            setpoint_x=[math.cos(setpoint_rad)],
            setpoint_y=[math.sin(setpoint_rad)],
            position_x=[math.cos(position)],
            position_y=[math.sin(position)]
        )        
        animation_source.stream(animation_data, 1)

    def update_dashboard():        
        global data
        #print(len(data['ts']))
        if len(data['ts']) > 0:
            source.stream(data, int(update_frequency*window))
            update_animation(data['setpoint'][-1], data['position'][-1])
            data = get_empty_data(process, controls)

    model_controls = row(*[controls[x] for x in ['motor', 'ratio', 'n_motors', 'cof', 'mass', 'length']],   
        sizing_mode="stretch_width")       
    controls_column = column(*(row(
        controls[x], HelpButton(tooltip=Tooltip(content=control_help[x], position='left')), sizing_mode="stretch_width")
        for x in ['f', 'p', 'i', 'izone', 'd', 'setpoint']), model_controls, sizing_mode="stretch_width")

    doc.add_root(
            column(
                row(
                    controls_column, 
                    column(p_animation, reset_button, reflect_button, sizing_mode="fixed"), 
                    sizing_mode="stretch_width"
                ), 
                p_mechanics, p_voltage, p_torque, sizing_mode="stretch_both"))

    # Add a periodic callback to be run every 500 milliseconds
    doc.add_periodic_callback(update_data, 1000.0 / update_frequency)
    doc.add_periodic_callback(update_dashboard, 1000.0 / frame_rate)
    doc.title = "PID demo"

#start_profiling()
bkapp(curdoc())
#atexit.register(stop_profiling)