import RPi.GPIO as GPIO
from time import sleep

# Motor GPIO pins
Motor_Dir = 8  # Motor direction pin
Motor_Step = 10  # Motor step (or enable) pin

# Encoder GPIO pins
Enc_A = 11
Enc_B = 13

# Target steps
target_steps = 100

def init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(Motor_Dir, GPIO.OUT)
    GPIO.setup(Motor_Step, GPIO.OUT)
    GPIO.setup(Enc_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Enc_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def motor_step():
    """Performs a single step for the motor."""
    GPIO.output(Motor_Step, GPIO.HIGH)
    sleep(0.01)  # Adjust step duration as needed
    GPIO.output(Motor_Step, GPIO.LOW)
    sleep(0.01)  # Adjust pause between steps as needed

def motor_forward(steps):
    """Moves the motor forward a specific number of steps."""
    GPIO.output(Motor_Dir, GPIO.HIGH)
    for _ in range(steps):
        motor_step()

def read_encoder():
    """Reads the current state of the encoder."""
    return GPIO.input(Enc_A), GPIO.input(Enc_B)

def measure_steps():
    """Measures steps using the encoder by polling its state changes."""
    last_state = read_encoder()
    count = 0

    while count < target_steps:
        current_state = read_encoder()
        if current_state != last_state:
            count += 1
            last_state = current_state
        sleep(0.005)  # Small delay to avoid missing encoder changes

    return count

def main():
    init()
    print("Moving motor forward, attempting to measure with encoder...")
    motor_forward(target_steps)  # Command the motor to move forward 100 steps
    measured_steps = measure_steps()  # Attempt to measure these steps with the encoder
    print(f"Motor movement attempted for {target_steps} steps, measured {measured_steps} steps.")
    GPIO.cleanup()

if __name__ == '__main__':
    main()
