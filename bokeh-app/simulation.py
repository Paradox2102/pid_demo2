import random
import math
import itertools
from statistics import mean

from process import Process
from constants import update_frequency, window
from math_util import radians_to_degrees

def is_settled(errors, thumb, steady_state_interval):
    max_error = min_error = errors[-1]
    for j, error in reversed(list(itertools.islice(enumerate(errors), thumb, len(errors)-1))):
        max_error = max(error, max_error)
        min_error = min(error, min_error)
        if max_error - min_error > steady_state_interval:
            return (False, j + 1)
    #print(dict(max_error=max_error, min_error=min_error, thumb=thumb, steady_state_interval=steady_state_interval,
    #    len=len(errors)-thumb, errors=len(errors)))
    return (True, thumb)


def simulate(process_init, initial_position=None):
    process = Process(now=0)
    process_init(process)
    if initial_position is None:
        initial_position = random.uniform(-math.pi, math.pi)
    process.reset(initial_position)
    initial_error = process.pid._calculate_difference(process.pid.setpoint - initial_position)
    overshoot = 0
    overshoot_index = None
    dt = 1.0 / update_frequency
    scan_window = window * update_frequency * 2
    times = itertools.count(start=dt, step=dt)
    thumb = 0
    steady_state_interval = abs(initial_error) * 0.02 * 2 # 2% either way
    errors = [ initial_error ]
    for i, time in enumerate(times, start=1):
        result = process.update(now=time)
        position = result['position']
        error = process.pid._calculate_difference(process.pid.setpoint - position)
        #print(dict(i=i, time=time, position=position, error=error))
        if abs(error) > abs(initial_error) or time > window * 100 or initial_error == 0:
            return dict(
                settled=False,
                initial_position=initial_position,
                initial_position_deg=radians_to_degrees(initial_position),
                final_time=time,
            )        
        assert i == len(errors)
        errors.append(error)
        if initial_error > 0:
            error = -error
        if error > overshoot:
            overshoot = error
            overshoot_index = i
            scan_window = max(overshoot_index, scan_window)
        if i - thumb > scan_window: # check for settling
            (settled, thumb) = is_settled(errors, thumb, steady_state_interval)
            if settled:
                return dict(
                    settled=True,
                    steady_state_error=abs(mean(errors[thumb:-1]) / initial_error),
                    overshoot=abs(overshoot / initial_error),
                    settling_time=thumb * dt,
                    initial_position=initial_position,
                    initial_position_deg=radians_to_degrees(initial_position),
                    final_time=time,
                )