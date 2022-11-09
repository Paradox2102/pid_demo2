# pid_demo2

Simple demo of PID controller for arm.

Inspired by: https://www.youtube.com/watch?v=qKy98Cbcltw

Tuning a PID controller that will hold an arm out horizontally is, perhaps, the hardest possible configuration.
The torque from gravity is at a maximum, so pushing up too hard is unstable.  Feedforward is not going to be enough.

While I have tried to make this a reasonable physics simualtor, you should not use it to select gear ratios.

## Quickstart

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Paradox2102/pid_demo2/main?urlpath=%2Fproxy%2F5006%2Fbokeh-app)

1. Click on the "Launch Binder" badge above.  Open in a new window so you can keep reading these instructions.  It may take few minutes to start up, so do it now.
1. Select a BAG motor, with a 150 gear ratio and a mass of 5kg.
1. Increase `f` until the arm is approaching horizontal but not spinning.  
   * Use the "Reset Arm" button to restart if things start going too fast. 
   * Add a little bit of `d` to slow things down.
1. Add some `p` to pull it towards the setpoint, but avoid too much overshoot.
1. If it's not quite getting there, add some `i`.
    * If your residual error is more than 20°, you may need to increase the `izone`.  If less, then you can decrease it.
    * Try to add the minimum `i` you can get away with because this can also increase overshoot.
1. Once you have the arm horizontal and steady, gently tune the `f` to match the total line on the voltage chart (or slightly below).
1. Use the "Reflect Setpoint" button to flip the arm from side to side.  Is it getting to the new setpoint quickly?  Is it stopping in time? 
   * Tune the `d` to reduce overshoot without slowing things down.
1. Click "Analyze" to get a report on how well your settings work in terms of overshoot, settling time, and steady state error.
   * A little overshoot is usually acceptable, but keep it under 2%.
   * Try to get your settling time down as low as possible.  Can you do it in less than a second?
   * You want your steady state error to be zero, or close to it.   What size of error is too small to affect gameplay?
1. Try doubling the mass of the arm and see if your settings still work.
1. Will the same settings work to bring the arm to a different angle, like straight up?
1. Did we pick the best gear ratio?
1. What if we used a different motor?

## Parts of the interface

## Scenario cnfiguration

![Selectors for motor, gear ratio, number of motors, coefficient of friction, gearbox efficiency, arm mass, and arm length](images/configuration_controls.png)

This can be used to configure the robot arm we're modelling.

## PID controls

![Sliders for f, p, i, izone, d, and setpoint](images/main_controls.png)

These are the controls that allow you to tune the feedforward and PID feedback controller.

## Animation

![Animation of swinging arm, with buttons "Reset Arm", Reflect Setpoint", and "Analyze"](images/animation_with_buttons.png)

This shows a real-time view of the robot arm.

The "Reset Arm" button points the arm straight down, and gives it zero velocity.

The "Reflect Setpoint" button reflects the setpoint around a vertical axis.

The "Analyze" button reports details of overshoot, settling time, and steady state error.

## Mechanics chart

![Chart showing setpoint, position, velocity and acceleration](images/chart_mechanics.png)

## Voltage chart
![Chart showing voltages from F, P, I, D and total](images/chart_voltage.png)

## Torque chart
![Chart showing torque from motor, gravity, and friction](images/chart_torque.png)

## PID internals chart
![Chart showing the error, error rate, and accumulated error](images/chart_pid.png)