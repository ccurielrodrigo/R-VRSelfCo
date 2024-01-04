# Imports
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
from time import sleep

# Initialize GPIO pins
DELAY_BETWEEN_STEPS = 0.0005  # Adjust this value for speed control
CYCLES = 500

# Direction pin from controller
DIR = 10
# Step pin from controller
STEP = 8
# 0/1 used to signify clockwise or counterclockwise.
CW = 1
CCW = 0

# Setup pin layout on PI
GPIO.setmode(GPIO.BOARD)

# Establish Pins in software
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)

# Set the first direction you want it to spin
GPIO.output(DIR, CW)

# Instance the app
app = Flask(__name__)

# Global variable for motor status
motor_status = False

# Function to toggle motor
def toggle_motor():
    global motor_status
    motor_status = not motor_status
    if motor_status:
        # Code to start the motor
        GPIO.output(DIR, CW)

        # Run for 200 steps at a speed determined by DELAY_BETWEEN_STEPS
        for x in range(CYCLES):
            GPIO.output(STEP, GPIO.HIGH)
            sleep(DELAY_BETWEEN_STEPS)
            GPIO.output(STEP, GPIO.LOW)
            sleep(DELAY_BETWEEN_STEPS)
        pass
    else:
    	# Code to stop the motor here
        GPIO.output(DIR, CCW)
        for x in range(CYCLES):
            GPIO.output(STEP, GPIO.HIGH)
            sleep(DELAY_BETWEEN_STEPS)
            GPIO.output(STEP, GPIO.LOW)
            sleep(DELAY_BETWEEN_STEPS)
        pass

# Endpoints
@app.route('/')
def index():
    templateData = {
        'title': 'Motor Control',
        'motor_status': 'On' if motor_status else 'Off'
    }
    return render_template('index.html', **templateData)

@app.route('/toggle_motor', methods=['POST'])
def handle_toggle_motor():
    toggle_motor()
    return 'On' if motor_status else 'Off'

# Runtime configuration
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
