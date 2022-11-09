# pid_demo2

Simple demo of PID controller for arm.

Inspired by: https://www.youtube.com/watch?v=qKy98Cbcltw

Tuning a PID controller that will hold an arm out horizontally is, perhaps, the hardest possible configuration.
The torque from gravity is at a maximum, so pushing up too hard is unstable.  Feedforward is not going to be enough.

While I have tried to make this a reasonable physics simualtor, you should not use it to select gear ratios.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Paradox2102/pid_demo2/main?urlpath=%2Fproxy%2F5006%2Fbokeh-app)
