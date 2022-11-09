# pid_demo2

Simple demo of PID controller for arm.

Inspired by: https://www.youtube.com/watch?v=qKy98Cbcltw

Tuning a PID controller that will hold an arm out horizontally is, perhaps, the hardest possible configuration.
The torque from gravity is at a maximum, so pushing up too hard is unstable.  Feedforward is not going to be enough.

While I have tried to make this a reasonable physics simualtor, you should not use it to select gear ratios.

## Quickstart

1. Click on the "Launch Binder" badge below.  Open in a new window so you can keep reading these instructions.  It may take few minutes to start up, so do it now.
1. Select a BAG motor, with a 150 gear ratio and a mass of 5kg.
1. Increase `f` until the arm is approaching horizontal but not spinning.  
   * Use the "Reset Arm" button to restart if things start going too fast. 
   * Add a little bit of `d` to slow things down.
1. Add some `p` to pull it towards the setpoint, but avoid too much overshoot.
1. If it's not quite getting there, add some `i`.
    * If your residual error is more than 20°, you may need to increase the `izone`.
    * Try to add the minimum `i` you can get away with because this can also increase overshoot.
1. Once you have the arm horizontal and steady, gently tune the `f` to match the total line on the voltage chart
1. Use the "Reflect Setpoint" button to flip the arm from side to side.  Is it getting to the new setpoint quickly?  Is it stopping in time? 
   * Tune the `d` to reduce overshoot without slowing things down.
1. Click "Analyze" to get a report on how well your settings work in terms of overshoot, settling time, and steady state error.
   * A little overshoot is usually acceptable, but keep it under 5%.
   * Try to get your settling time down as low as possible.
   * You want your steady state error to be zero, or close to it.   
1. Try doubling the mass of the arm and see if your settings still work.
1. Will the same settings work to bring the arm to a different angle, like straight up?
1. Did we pick the best gear ratio?
1. What if we used a different motor?

![Screenshot of PID demo tool.  There are sliders for PIDF, IZone and Setpoint, and selectors for motor, gear ratio, number of motors, coefficient of friction, gearbox efficiency, arm mass, and arm length.  Charts show an animation of a swinging arm, mechanical properties, voltages, and torques.](images/screenshot.png)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Paradox2102/pid_demo2/main?urlpath=%2Fproxy%2F5006%2Fbokeh-app)
