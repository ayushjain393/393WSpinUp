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
RF = Motor(Ports.PORT19, GearSetting.RATIO_6_1)
RB = Motor(Ports.PORT20, GearSetting.RATIO_6_1)
'''Reversing the right side motors is not required because they are mounted 
in the orientation directly opposite of left side motors'''
LF = Motor(Ports.PORT11, GearSetting.RATIO_6_1, True)
LB = Motor(Ports.PORT12, GearSetting.RATIO_6_1, True)
"""Control chassis during auton using left and right motorgroup rather than drivtrain,
 to have greater and more direct control over movement. Set stopping to brake for most consistency and 
 zero drift."""
stopping = BrakeType.COAST
Left_drive = MotorGroup(LF, LB)
Left_drive.set_stopping(stopping)
Right_drive = MotorGroup(RF, RB)
Right_drive.set_stopping(stopping)
#inertial 
IMU= Inertial(Ports.PORT14)
#both flywheel motors
Flywheel_1 = Motor(Ports.PORT15, GearSetting.RATIO_6_1)
Flywheel_2 = Motor(Ports.PORT16, GearSetting.RATIO_6_1) #using a motorgroup here will allow code to address both motors at once
Flywheel= MotorGroup(Flywheel_1, Flywheel_2)
Flywheel.set_velocity(600, VelocityUnits.RPM)
''' set stopping to coast because motor hold will make all of the power from 
the 3000 rpm flywheel will get redriected into motor. This way, motor will be more protected. 
Intake is also high speed, 600 rpm, so same for its motor'''
intake_1 = Motor(Ports.PORT18, GearSetting.RATIO_6_1)
intake_1.set_stopping(BrakeType.COAST)
#roller mech subsystem will be supported by optical sensor
optical = Optical(Ports.PORT6)
alliance_color = Color.RED
indexer = DigitalOut(brain.three_wire_port.a)
expansion_piston_1 = DigitalOut(brain.three_wire_port.b)
#set indexer state using variables so that it can be toggled easily
indexer_state = False
indexer.set(indexer_state)
#expansion blocker
blocker = DigitalOut(brain.three_wire_port.c)
blocker_state = False
blocker.set(blocker_state)
#Same for expansion
expansion_state = False
expansion_piston_1.set(expansion_state)
#endregion robot config#
IMU = Inertial(Ports.PORT14)
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
    wait(0.05,TimeUnits.SECONDS)
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
    #if expansion:
    expansion_state = not expansion_state
    expansion_piston_1.set(expansion_state)
roller_index = 0
#roller control macro for auton and driver
def spin_rollers(direction):
    #calling the global instance of variable into the scope of function
    global roller_index
    speeds = [0,250]
    roller_index +=1
    # make sure that index stays less than 2 and loops back to sero
    roller_index %= 2
    # index will pull intended flywheel speed from list and spin at new speed
    intake_1.spin(direction, speeds[roller_index], VelocityUnits.RPM)
    controller.screen.set_cursor(2,1)
    controller.screen.clear_row
    controller.screen.print("intake speed%7.2f"%(speeds[roller_index]*50))
    
#expansion blocker trigger
def reject_ad():
    global blocker_state
    blocker_state =  not blocker_state
    blocker.set(blocker_state)
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
    global voltage
    global sped
    state+= 1
    state%= 2
    if state == 0:
        Flywheel.stop()
        update_values(0,0)
    if state == 1:
        #Flywheel_1.spin(FORWARD,voltage, VOLT)
        #Flywheel_2.spin(FORWARD, voltage, VOLT)
        update_values(sped, voltage)
         # Controller will notify driver of current speed
        controller.screen.set_cursor(1,1)    
        controller.screen.clear_row
        controller.screen.print("flywheel speed:%7.2f"%(sped))
    
index = 0
voltage=0.7
sped=390
def flywheel_toggle():
    #calling the global instance of variable into the scope of function
    global index
    global voltage
    speeds = [0.7, 0.75, 1]
    speed= [390, 450, 600]
    index +=1
    # make sure that index stays less than three and loops back to sero
    index %= 3
    # index will pull intended flywheel speed from list and spin at new speed
    global state
    voltage = speeds[index]
    sped= speed[index]
    if state == 1:
        #Flywheel_1.spin(FORWARD,voltage, VOLT)
        #Flywheel_2.spin(FORWARD, voltage, VOLT)
        update_values(sped, voltage)
         # Controller will notify driver of current speed    
    # Controller will notify driver of current speed    
    controller.screen.set_cursor(1,1)
    controller.screen.clear_row
    controller.screen.print("flywheel speed:%7.2f"%(sped))
# intake on and off toggle
# intake on and off toggle
intake_index = 0
def intake_toggle(direction):
    #calling the global instance of variable into the scope of function
    global intake_index
    speeds = [0,12]
    intake_index +=1
    # make sure that index stays less than 2 and loops back to sero
    intake_index %= 2
    # index will pull intended flywheel speed from list and spin at new speed
    intake_1.spin(direction, speeds[intake_index], VOLT)
    controller.screen.set_cursor(2,1)
    controller.screen.clear_row
    controller.screen.print("intake speed%7.2f"%(speeds[intake_index]*50))
#regiontbhloop
def sign(num):
    z=int(num)
    if z== 0:
        return 1
    if z/abs(z) == 1:
        return 1
    elif z/abs(z) == -1:
        return -1
    else:
        return 0
 #Take back half variable
TBH=0
#predicted power variable to substitute for first zero crossing
OG_TBH= 0
#integral gain, usually very low, 
# higher gain= lower spin up times, but also more overshoot and settle time 
KI=0.00025
#deviation of velocity from desired
error=0
#power not scaled, 0-1.0
power=0
#store previous error
prev_error = 0
# check for first zero crossing
first_zero_crossing = False
#desired speed
SPEED = 0
#based on jpearman vexforum post. jpearman is op
#loop will keep running in thread, even when speed is zero. 
# update function will change global variables mid loop
def FlywheelTBH():
    global TBH, OG_TBH, KI, error, power, prev_error, prev_power, first_zero_crossing, SPEED
    #calcualte error
    error = SPEED -  Flywheel.velocity()
    #adjust power
    power= power+(error*KI)
    if SPEED > 0 and error <5:
        brain.screen.clear_screen()
        brain.screen.set_cursor(1,1)
        brain.screen.print(power)
    # keep power positive and under 1.0
    if power>1.0:
       power=1.0
    if power<0.0:
        power=0
    #check zero crossing 
    if sign(error) != sign(prev_error):
        if first_zero_crossing==True:
            brain.screen.print(power)
            #replace power with predicted drive
            power = OG_TBH
            first_zero_crossing = False
        else:
            #essentially half the power
            power = 0.5*(power+TBH)
        #store power and error from previous loop for the next halving
        TBH= power

        prev_error=error
#tbh driver control function to update speed.
def update_values(speed, og_tbh):
    global TBH, OG_TBH, KI, error, power, prev_error, prev_power, first_zero_crossing, SPEED
    #required open loop value
    OG_TBH= og_tbh
    #update desired speed
    SPEED = speed
    #update error and prev_error for correct detection of zero crossing
    error= SPEED - Flywheel.velocity()
    prev_error= error
    #reset zero cross
    first_zero_crossing = False
    #reset tbh
    TBH = 0
#final loop, combine everything in one separately running task
def tbhloop():
    final_power = 0
    while True:    
        #make calculations
        FlywheelTBH()
        #scale power
        final_power = power*12
        #limit power to 12V
        if final_power> 12.0:
            final_power = 12.0
        if final_power < 0:
            final_power = 0
        #apply power
        Flywheel_1.spin(FORWARD, final_power, VOLT)
        Flywheel_2.spin(FORWARD, final_power, VOLT)
        wait(25, MSEC)
#endregionrr
   
        

def drivercontrol():
    update_values(0,0)
    Left_drive.set_stopping(BrakeType.COAST)
    Right_drive.set_stopping(BrakeType.COAST)
    #reset brain timer so that there are no clock inconsistencies due to  pause between auton and driver
    brain.timer.reset()
    global alliance_color
    while True:
        #arcade drive controls, left stick axis4 controls turning, right stick axis2 controls front/back movement
        LF.spin(DirectionType.FORWARD, (controller.axis2.position()+controller.axis4.position())*0.12, VOLT)
        LB.spin(DirectionType.FORWARD, (controller.axis2.position()+controller.axis4.position())*0.12, VOLT)
        RF.spin(DirectionType.FORWARD, (controller.axis2.position()-controller.axis4.position())*0.12, VOLT)
        RB.spin(DirectionType.FORWARD, (controller.axis2.position()-controller.axis4.position())*0.12, VOLT)

    
        
        #special expansion code will only run if there are 10 secs of driver control left/95 seconds on clock
        #if int(brain.timer.value())>= 95:
            #expansion = True       
# auton toolkit for skills and driver (fwd/reverse PD, turn PD, roller macro, pneumatics toggle)
#drive fwd/rev PD input negative values to drive reverse
def inches_to_ticks(inches):
    inches_per_rev  = 12.9525
    motor_to_wheel= 3/7
    true_travel= inches_per_rev*motor_to_wheel
    ticks_per_inches= 300/true_travel
    total_ticks = inches*ticks_per_inches
    return total_ticks

# auton toolkit for skills and driver (fwd/reverse PD, turn PD, roller macro, pneumatics toggle)
#drive fwd/rev PD input negative values to drive reverse
def drive_for(target, t_kp, t_kd, slew, heading):
    Right_drive.reset_position()
    Left_drive.reset_position()
    slew_on = False
    kp = t_kp
    kd = t_kd
    error = 0
    prev_error = 0
    power = 0
    count = 0
    target= inches_to_ticks(target)
    IMU.reset_rotation()
    #head_error=
    while True:
        #store prev_error  and prev_powerfor derivative
        prev_error = error
        prev_power = power
        heading_error = IMU.rotation()-heading
        #drivetrain IME  values
        error = target-(Left_drive.position(RotationUnits.RAW)+Right_drive.position(RotationUnits.RAW))/2
        derivative = error-prev_error
        power = error*kp+derivative*kd
        correction = heading_error/360
        if slew_on:
            if abs(power)<= abs(prev_power)+abs(slew):
                slew_on = False
            else:
                power = prev_power + slew
        #motor groups do not take voltage parameters, but individual motors do
        LB.spin(FORWARD, power+correction, VOLT)
        LF.spin(FORWARD, power+correction, VOLT)
        RB.spin(FORWARD, power-correction, VOLT)
        RF.spin(FORWARD, power-correction, VOLT)
        print( power)
        if error <=2:
            count +=1
        if count == 5:
            break   
        sleep(2, TimeUnits.MSEC)

def turn_for(target, t_kp, t_kd, slew):
    Right_drive.reset_position()
    Left_drive.reset_position()
    slew_on = False
    kp = t_kp
    kd = t_kd
    prev_error= 0 
    #if desired turn is counter clockwise
    error = 0
    power = 0
    prev_power = 0
    IMU.reset_rotation()
    count = 0
    while True:
        #store prev_error  and prev_powerfor derivative
        prev_error = error
        #drivetrain IME  values
        error = target - IMU.rotation()
        derivative = error-prev_error
        power = error*kp+derivative*kd      
        brain.screen.clear_screen()
        brain.screen.set_cursor(1,1)
        brain.screen.print(power)
        if slew_on:
            if abs(power)<= abs(prev_power)+abs(slew):
                slew_on = False
            else:
                power = prev_power + slew
        LF.spin(FORWARD, power, VOLT)
        LB.spin(FORWARD,power , VOLT)
        RF.spin(FORWARD,-power, VOLT)
        RB.spin(FORWARD, -power, VOLT)
        if abs(error) <=1:
            count +=1
        if count >=5:
            break            
        sleep(2, MSEC)
   

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
    update_values(450, 0.78)
    intake_1.spin(FORWARD, 12, VOLT)
    drive_for(18, )
    turn_for(-45, 0.5, 0, 0)
    indexer_toggle()
    indexer_toggle()
    turn_for(30, 0.5, 0,0)
    update_values(0,0)
    drive_for(45, )
    update_values(450, 0.78)
    turn_for(-15, 0.5, 0,0)
    indexer_toggle()
    indexer_toggle()
    indexer_toggle()
    turn_for(-15, 0.5, 0,0)
    drive_for(60,)
    turn_for(15, 0.5,0,0)
    drive_for(3,)
    intake_1.spin_for(REVERSE, 250, DEGREES, 600, RPM)
    
    

    #Right_drive.spin_for(DirectionType.REVERSE, 401, RotationUnits.DEG)
        #extra section for part that will be added to skills
    
def pre_auton():
    IMU.calibrate()
    while IMU.is_calibrating():
        wait(50,MSEC)
    IMU.set_turn_type(RIGHT)    
    brain.screen.print("done")    
pre_auton()
competition = Competition(drivercontrol,autonomous)
#callback function makes sure indexer only moves onces when the button is pressed and does not reset
controller.buttonR1.pressed(indexer_toggle)
# roller macro     
controller.buttonY.pressed(spin_rollers,(DirectionType.FORWARD,))
#flywheel speed toggle
controller.buttonUp.pressed(flywheel_toggle)
#flywheel on->off->on
controller.buttonR2.pressed(flywheel_on_off)
#expansion will only run at 1:50
controller.buttonB.pressed(expansion_toggle)
# intake toggle. direction arguements allow the same function to be 
# used for intake and outtake, but different directions
controller.buttonL1.pressed(intake_toggle,(DirectionType.FORWARD,))
controller.buttonL2.pressed(spin_rollers,(DirectionType.REVERSE,))
#toggle between motor brake setting and motor hold setting
controller.buttonA.pressed(brake_on_off)
#auton dev only, comment out for match
controller.buttonDown.pressed(return_values)
#expansion blocker trigger
controller.buttonLeft.pressed(reject_ad)
#flywheel control does not interfere with rest of drivercontrol or auton
flywheel = Thread(tbhloop)

    