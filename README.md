# pid_demo2

Simple demo of PID controller for arm.

Inspired by: https://www.youtube.com/watch?v=qKy98Cbcltw

Tuning a PID controller that will hold an arm out horizontally is, perhaps, the hardest possible configuration.
The torque from gravity is at a maximum, so pushing up too hard is unstable.  Feedforward is not going to be enough.

While I have tried to make this a reasonable physics simualtor, you should not use it to select gear ratios.

## Quickstart

1. Click on the badge below.  It may take few minutes to start up.
2. Select a BAG motor, with a 150 gear ratio and a mass of 5kg.
3. Increase `f` until the arm is approaching horizontal but not spinning.  Use the "Reset Arm" button to restart if things are going too fast.
4. Add a little bit of `d` to slow things down.
5. Add some `p` to pull it towards the setpoint.
6. If it's not quite getting there, add some `i`.
7. If your residual error is more than 20°, you may need to increase the `izone`.
7. Once you have the arm horizontal and steady, retune the `f` to match the total voltage.
8. Use the "Reflect Setpoint" button to move the arm from side to side.  Is it getting the to new setpoint quickly and stopping in time? 
9. Click "Analyze" to get a report on how well your settings work in terms of overshoot, settling time, and steady state error.
10. See if your settings still work when the arm weighs twicr as much.
11. Will the same settings work to bring the arm to a different angle?

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Paradox2102/pid_demo2/main?urlpath=%2Fproxy%2F5006%2Fbokeh-app)
