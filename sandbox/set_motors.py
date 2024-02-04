import RPi.GPIO as GPIO
from time import sleep

# GPIO pins
Enc_A = 17
Enc_B = 27

# Position counter
counter = 0

# Encoder state
last_A = 0
last_B = 0

# Motor
Motor_Setp = 15,                        
Motor_Dir =  14

# Sleep time
slee_time = 0.0005
bouncing_time = 0.005
steps = 100

def init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Enc_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Enc_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Motor_Setp, GPIO.OUT)
    GPIO.setup(Motor_Dir, GPIO.OUT)

    # For direction
    GPIO.output(Motor_Dir, 1)


def read_encoder():
    return GPIO.input(Enc_A), GPIO.input(Enc_B)

def update_position(A, B):
    global counter, last_A, last_B
    if A != last_A or B != last_B:  # Only update on change
        if A == 1 and B == 0 and last_A == 0:  # Clockwise
            counter += 1
        elif A == 0 and B == 1 and last_B == 0:  # Counter-clockwise
            counter -= 1
        last_A, last_B = A, B

def main():
    init()
    print("Monitoring rotary encoder...")
    try:
        while True:
            A, B = read_encoder()
            update_position(A, B)
            print(f"Position: {counter}")
            if counter < steps:
                GPIO.output(Motor_Setp, GPIO.HIGH)
                sleep(slee_time)
                GPIO.output(Motor_Setp, GPIO.LOW)

            sleep(bouncing_time)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Program exited cleanly")

if __name__ == '__main__':
    main()
