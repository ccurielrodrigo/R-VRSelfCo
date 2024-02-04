import RPi.GPIO as GPIO
from time import sleep

# Motor GPIO pins
Motor_Dir = 8  # Motor direction pin
Motor_Step = 10  # Motor step (or enable) pin

# Encoder GPIO pins
Enc_A = 19
Enc_B = 21

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
    for step in range(steps):
        motor_step()
        # After each step, print the encoder state to verify its reading
        enc_state = read_encoder()
        print(f"Step {step+1}: Encoder State: A={enc_state[0]}, B={enc_state[1]}")

def read_encoder():
    """Reads the current state of the encoder."""
    return GPIO.input(Enc_A), GPIO.input(Enc_B)

def main():
    init()
    print("Moving motor forward, monitoring encoder states...")
    motor_forward(target_steps)  # Command the motor to move forward 100 steps
    print("Motor movement complete. Check the log for encoder states.")
    GPIO.cleanup()

if __name__ == '__main__':
    main()
