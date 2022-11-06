import math

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
