# Imports
from flask import Flask, render_template, request
import RPi.GPIO as GPIO

# Initialize GPIO pins
GPIO.setmode(GPIO.BOARD)
DIR_PIN = 10  # Replace with your actual GPIO pin numbers
STEP_PIN = 8  # Replace with your actual GPIO pin numbers
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

# Instance the app
app = Flask(__name__)

# Global variable for motor status
motor_status = False

# Function to toggle motor
def toggle_motor():
    global motor_status
    motor_status = not motor_status
    if motor_status:
        # Code to start the motor here
        pass
    else:
        # Code to stop the motor here
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
