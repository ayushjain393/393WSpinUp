 #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       ayush                                                        #
# 	Created:      Mon Sep 05 2022                                              #
# 	Description:  393W Spin up V1                                         #
#                                                                              #
# ---------------------------------------------------------------------------- #

# Library
from vex import*
# Brain should be defined by default
brain=Brain()
controller = Controller(ControllerType.PRIMARY)
#blocker for all expansion mechs, so that pneumatics will not actuate before 1:50 if button is pressed
expansion = False
#region robot config#
#init all  motors/sensors/pneumatics here#
#reverse left side motors to account for orientation and gear ratio
RF = Motor(Ports.PORT10, GearSetting.RATIO_6_1)
RB = Motor(Ports.PORT9, GearSetting.RATIO_6_1)
'''Reversing the right side motors is not required because they are mounted 
in the orientation directly opposite of left side motors'''
LF = Motor(Ports.PORT11, GearSetting.RATIO_6_1, True)
LB = Motor(Ports.PORT20, GearSetting.RATIO_6_1, True)
"""Control chassis during auton using left and right motorgroup rather than drivtrain,
 to have greater and more direct control over movement. Set stopping to brake for most consistency and 
 zero drift."""
stopping = BrakeType.COAST
Left_drive = MotorGroup(LF, LB)
Left_drive.set_stopping(stopping)
Right_drive = MotorGroup(RF, RB)
Right_drive.set_stopping(stopping)

#both flywheel motors
Flywheel_1 = Motor(Ports.PORT3, GearSetting.RATIO_6_1)
Flywheel_2 = Motor(Ports.PORT4, GearSetting.RATIO_6_1) #using a motorgroup here will allow code to address both motors at once
Flywheel= MotorGroup(Flywheel_1, Flywheel_2)
Flywheel.set_velocity(600, VelocityUnits.RPM)
''' set stopping to coast because motor hold will make all of the power from 
the 3000 rpm flywheel will get redriected into motor. This way, motor will be more protected. 
Intake is also high speed, 600 rpm, so same for its motor scrabadooshy mandakoolooshy iz keuwl''' 
intake_1 = Motor(Ports.PORT5, GearSetting.RATIO_6_1)
intake_1.set_stopping(BrakeType.COAST)
#roller mech subsystem will be supported by optical sensor
optical = Optical(Ports.PORT6)
alliance_color = Color.RED
indexer = DigitalOut(brain.three_wire_port.a)
expansion_piston_1 = DigitalOut(brain.three_wire_port.b)
#set indexer state using variables so that it can be toggled easily
indexer_state = True
indexer.set(indexer_state)
#Same for expansion
expansion_state = True

#endregion robot config#

# this function will be used with a button callback, so that indexer can be 
#toggled with only one button instead of two
shots = 0
def indexer_toggle():
    # indexer_state variable is outside of scope of function,
    # so it needs to be declared global from inside
    global indexer_state
    global shots
    #reversing the piston's state, regardless of current position
    shots+=1
    indexer_state= not indexer_state
    indexer.set(indexer_state)
    wait(0.3,TimeUnits.SECONDS)
    indexer_state = not indexer_state
    indexer.set(indexer_state)
    controller.screen.set_cursor(3,1)
    controller.screen.clear_row
    controller.screen.print("shots:%7.2f"%shots)
    
# same idea for expansion mech. Will be inserted into a callback for 
# entire 2:00, but expansion variable will set to false until 1:50, and 
# then pneumatics will be able to execute.
def expansion_toggle():
    global expansion_state
    if expansion:
        expansion_state = not expansion_state
        expansion_piston_1.set( expansion_state)
roller_index = 0
#roller control macro for auton and driver
def spin_rollers():
    #calling the global instance of variable into the scope of function
    global roller_index
    speeds = [0,300]
    roller_index +=1
    # make sure that index stays less than 2 and loops back to sero
    roller_index %= 2
    # index will pull intended flywheel speed from list and spin at new speed
    intake_1.spin(FORWARD, speeds[roller_index], VelocityUnits.RPM)
    
# function to change braketype betwen hold with has an active PID to return motor to a position, 
# and brake which simply resists movement, and can be moved away from original position
brake_index = 0
def brake_on_off():
    global stopping, brake_index
    breaktypes = [BrakeType.BRAKE, BrakeType.COAST]
    brake_index +=1
    brake_index %= 2
    Right_drive.set_stopping(breaktypes[brake_index])
    Left_drive.set_stopping(breaktypes[brake_index])


#flywheel speed toggle for different shooting ranges
# index variable needs to stay global, so that it does not reset after each callback
state = 0
def flywheel_on_off():
    global state
    state+= 1
    state%= 2
    if state == 0:
        Flywheel.stop()
    if state == 1:
        Flywheel.spin(FORWARD)
    
index = 0
def flywheel_toggle():
    #calling the global instance of variable into the scope of function
    global index
    speeds = [0, 380, 450, 600]
    index +=1
    # make sure that index stays less than three and loops back to sero
    index %= 4
    # index will pull intended flywheel speed from list and spin at new speed
    Flywheel.set_velocity(speeds[index], VelocityUnits.RPM)
    # Controller will notify driver of current speed    
    controller.screen.clear_row
    controller.screen.set_cursor(1,1)
    controller.screen.print("flywheel speed:%7.2f"%(speeds[index]))
# intake on and off toggle
intake_index = 0
def intake_toggle(direction):
    #calling the global instance of variable into the scope of function
    global intake_index
    speeds = [0,600]
    intake_index +=1
    # make sure that index stays less than 2 and loops back to sero
    intake_index %= 2
    # index will pull intended flywheel speed from list and spin at new speed
    intake_1.spin(direction, speeds[intake_index], VelocityUnits.RPM)
    controller.screen.set_cursor(2,1)
    controller.screen.clear_row
    controller.screen.print("intake speed%7.2f"%(speeds[intake_index]))

    
   
        

def drivercontrol():
    #reset brain timer so that there are no clock inconsistencies due to  pause between auton and driver
    brain.timer.reset()
    global alliance_color
    while True:
        #arcade drive controls, left stick axis4 controls turning, right stick axis2 controls front/back movement
        Left_drive.spin(DirectionType.FORWARD,controller.axis2.position()+controller.axis4.position(), VelocityUnits.PERCENT)
        Right_drive.spin(DirectionType.FORWARD, controller.axis2.position()-controller.axis4.position(), VelocityUnits.PERCENT)
        #special expansion code will only run if there are 10 secs of driver control left/95 seconds on clock
        #if int(brain.timer.value())>= 95:
            #expansion = True       
# auton toolkit for skills and driver (fwd/reverse PD, turn PD, roller macro, pneumatics toggle)
#drive fwd/rev PD input negative values to drive reverse
def drive_for(target, t_kp, t_kd, slew):
    Right_drive.reset_position()
    Left_drive.reset_position()
    slew_on = True
    kp = t_kp
    kd = t_kd
    error = 0
    prev_error = 0
    power = 0
    count = 0
    while True:
        #store prev_error  and prev_powerfor derivative
        prev_error = error
        prev_power = power
        #drivetrain IME  values
        error = target-(Left_drive.position(RotationUnits.DEG)+Right_drive.position(RotationUnits.DEG))/2
        derivative = error-prev_error
        power = error*kp+derivative*kd
        if slew_on:
            if abs(power)<= abs(prev_power)+abs(slew):
                slew_on = False
            else:
                power = prev_power + slew
        #motor groups do not take voltage parameters, but individual motors do
        LB.spin(FORWARD, power, VOLT)
        LF.spin(FORWARD, power, VOLT)
        RB.spin(FORWARD, power, VOLT)
        RF.spin(FORWARD, power, VOLT)
        if error <=2:
            count +=1
        if count == 28:
            break   
        sleep(10, TimeUnits.MSEC)
def turn_for(target, t_kp, t_kd, slew):
    Right_drive.reset_position()
    Left_drive.reset_position()
    slew_on = True
    kp = t_kp
    kd = t_kd
    left_error = 0
    prev_left_error = 0
    right_error = 0
    prev_right_error = 0
    left_power = 0
    right_power = 0
    count = 0
    while True:
        #store prev_error  and prev_powerfor derivative
        prev_left_error = left_error
        prev_left_power = left_power
        prev_right_error = right_error
        prev_right_power = right_power
        #drivetrain IME  values
        left_error = target - Left_drive.position(RotationUnits.DEG)
        right_error= target + Right_drive.position(RotationUnits.DEG)      
        left_derivative = left_error-prev_left_error
        right_derivative = right_error-prev_right_error
        left_power = left_error*kp+left_derivative*kd
        right_power = right_error*kp+left_derivative*kd
        
        #if slew_on:
            #if abs(power)<= abs(prev_power)+abs(slew):
                #slew_on = False
            #else:
                #power = prev_power + slew
        LF.spin(FORWARD, left_power, VOLT)
        LB.spin(FORWARD, left_power, VOLT)
        RF.spin(FORWARD,-right_power, VOLT)
        RB.spin(FORWARD, -right_power, VOLT)
        if abs((left_error)+abs(right_error))/2 <=2:
            count +=1
        if count == 28:
            break            


#returns encoder values so it is easy to plug and play in auton also 
#resets values after each check, so movements are not added up with prev encoder movements
def return_values():
    brain.screen.print(str(Left_drive.position(RotationUnits.DEG)))
    Left_drive.set_position(0, RotationUnits.DEG)
    brain.screen.new_line()
    brain.screen.print(str(Right_drive.position(RotationUnits.DEG)))
    Right_drive.set_position(0, RotationUnits.DEG)
    brain.screen.new_line()
    

#special auton develop toolkit returns encoder values of different subsystems 
# when robot is manualy moved through auton routine, so that coders can instantly plug in 
# values for a more accurate auton
def autonomous():
    #drive_for(10, 0.5,0, 0.5)
    brain.timer.reset()
    Left_drive.spin_for(DirectionType.FORWARD, 1437, RotationUnits.DEG,600, VelocityUnits.RPM,wait=False)
    Right_drive.spin_for(DirectionType.FORWARD, 14347,RotationUnits.DEG,600, VelocityUnits.RPM,wait=True )
    #intake_1.spin_for(DirectionType.REVERSE, 400, RotationUnits.DEG)
    #Left_drive.spin_for(DirectionType.REVERSE, 360, RotationUnits.DEG, 600, VelocityUnits.RPM, wait=False)
    #Right_drive.spin_for(DirectionType.REVERSE, 360, RotationUnits.DEG, 600, VelocityUnits.RPM, wait=True)
    #Left_drive.spin_for(DirectionType.FORWARD, 401, RotationUnits.DEG)
    #Right_drive.spin_for(DirectionType.REVERSE, 401, RotationUnits.DEG)
        #extra section for part that will be added to skills
    """for x in range(3):
        Left_drive.__spin_for_time(DirectionType.FORWARD, 2.5, TimeUnits.SECONDS, 600, VelocityUnits.RPM)
        Right_drive.__spin_for_time(DirectionType.FORWARD, 2.5, TimeUnits.SECONDS, 600, VelocityUnits.RPM)
        Left_drive.__spin_for_time(DirectionType.REVERSE, 1, TimeUnits.SECONDS, 600, VelocityUnits.RPM)
        Right_drive.__spin_for_time(DirectionType.REVERSE, 1, TimeUnits.SECONDS, 600, VelocityUnits.RPM)
        wait(2, TimeUnits.SEC)
    Left_drive.__spin_for_time(DirectionType.REVERSE,2, TimeUnits.SEC, 600, VelocityUnits.RPM) 
    Right_drive.__spin_for_time(DirectionType.REVERSE,2, TimeUnits.SEC, 600, VelocityUnits.RPM)   
    Left_drive.spin_for(DirectionType.REVERSE, 200.67, RotationUnits.DEG)
    Right_drive.spin_for(DirectionType.FORWARD, 200.67, RotationUnits.DEG)
    while True:
        if brain.timer.value() >= 50:
            controller.screen.print("expansion deploying!")
            expansion_piston_1.set(False)
            break"""

competition = Competition(drivercontrol,autonomous)
#callback function makes sure indexer only moves onces when the button is pressed and does not reset
controller.buttonR1.pressed(indexer_toggle)
# roller macro     
controller.buttonB.pressed(spin_rollers)
#flywheel speed toggle
controller.buttonUp.pressed(flywheel_toggle)
#flywheel on->off->on
controller.buttonR2.pressed(flywheel_on_off)
#expansion will only run at 1:50
controller.buttonL2.pressed(expansion_toggle)
# intake toggle. direction arguements allow the same function to be 
# used for intake and outtake, but different directions
controller.buttonL1.pressed(intake_toggle,(DirectionType.FORWARD,))
controller.buttonY.pressed(intake_toggle,(DirectionType.REVERSE,))
#toggle between motor brake setting and motor hold setting
controller.buttonA.pressed(brake_on_off)
#auton dev only, comment out for match
controller.buttonDown.pressed(return_values)
