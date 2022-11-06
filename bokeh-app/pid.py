from math_util import *

class PID:
    def __init__(self, p=0, i=0, d=0, izone=0, setpoint=0):
        self.last_err = None
        self.err_acc = 0
        self.continuous = False
        self.p = p
        self.i = i
        self.d = d
        self.izone = izone
        self.setpoint = setpoint
        
    def enable_continuous_input(self, minimum_input, maximum_input):
        self.continuous = True
        self.minimum_input = minimum_input
        self.maximum_input = maximum_input
        self.error_bound = (maximum_input - minimum_input) / 2.0
        
    def calculate(self, measurement, dt):
        err = self._calculate_difference(self.setpoint - measurement)
        p_output = self.p * err
        if dt is not None:
            assert self.last_err is not None, f"dt={dt}"
            d_err = self._calculate_difference(err - self.last_err) / dt
        else:
            d_err = 0
        self.last_err = err

        d_output = self.d * d_err

        #print(dict(dt=dt, d_err=d_err, err=err, err_acc=self.err_acc))
        
        if abs(err) < self.izone and dt is not None and self.i > 0:
            self.err_acc += err * dt
        else:
            self.err_acc = 0
        i_output = self.i * self.err_acc
        output = p_output + i_output + d_output # unclamped
        result = dict(output=output, p_output=p_output, d_output=d_output, i_output=i_output, err=err, d_err=d_err, err_acc=self.err_acc)
        assert set(result.keys()) == set(self.columns)
        return result
    
    def _calculate_difference(self, value):
        if self.continuous:
            return input_modulus(value, -self.error_bound, +self.error_bound)
        else:
            return value

    def set_p(self, value):
        self.p = value

    def set_i(self, value):
        self.i = value

    def set_d(self, value):
        self.d = value

    def set_izone(self, value):
        self.izone = value

    def set_setpoint(self, value):
        measurement = self.setpoint - self.last_err
        self.setpoint = value
        self.last_err = self._calculate_difference(self.setpoint - measurement)

    def reset(self):
        self.last_err = None

    @property
    def columns(self):
        return ['output', 'p_output', 'i_output', 'd_output', 'd_err', 'err', 'err_acc']
