import RPi.GPIO as GPIO
from time import sleep

# Encoder GPIO pins
Enc_A = 19
Enc_B = 21

# Motor GPIO pins (example pins, adjust according to your setup)
Motor_Dir = 8 # Motor direction pin
Motor_Step = 10  # Motor step (or enable) pin

# Position counter and target
counter = 0
target_position = 100  # Set this to your desired target position

# Encoder state
last_A = 0
last_B = 0

def init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(Enc_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Enc_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Motor_Dir, GPIO.OUT) 
    GPIO.setup(Motor_Step, GPIO.OUT)
    
    # Initialize interrupt handlers for encoder
    GPIO.add_event_detect(Enc_A, GPIO.RISING, callback=update_position)
    GPIO.add_event_detect(Enc_B, GPIO.RISING, callback=update_position)

def read_encoder():
    return GPIO.input(Enc_A), GPIO.input(Enc_B)

def update_position(channel):
    global counter, last_A, last_B
    A, B = read_encoder()
    if A != last_A or B != last_B:  # Only update on change
        if A == 1 and B == 0 and last_A == 0:  # Clockwise
            counter += 1
        elif A == 0 and B == 1 and last_B == 0:  # Counter-clockwise
            counter -= 1
    last_A, last_B = A, B
    adjust_motor()

def adjust_motor():
    error = target_position - counter
    if abs(error) > 0:
        if error > 0:
            motor_forward()
        else:
            motor_backward()
    else:
        stop_motor()

def motor_forward():
    GPIO.output(Motor_Dir, GPIO.HIGH)
    GPIO.output(Motor_Step, GPIO.HIGH)
    sleep(0.01)  # Adjust step duration as needed
    GPIO.output(Motor_Step, GPIO.LOW)

def motor_backward():
    GPIO.output(Motor_Dir, GPIO.LOW)
    GPIO.output(Motor_Step, GPIO.HIGH)
    sleep(0.01)  # Adjust step duration as needed
    GPIO.output(Motor_Step, GPIO.LOW)

def stop_motor():
    # Assumes LOW on Motor_Step stops the motor, adjust if necessary
    GPIO.output(Motor_Step, GPIO.LOW)

def main():
    init()
    print("Adjusting motor to match target position...")
    try:
        while True:
            sleep(0.1)  # Main loop delay, adjust as necessary for other tasks
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Program exited cleanly")

if __name__ == '__main__':
    main()
