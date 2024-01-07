'''
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
IMPORTS
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
'''
from flask import Flask, render_template, request
import RPi.GPIO as GPIO
from time import sleep


'''
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
GLOBAL INSTANCES
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
'''
# Direction and step pins (palm and dorso of the hand)
GPIO_PINS = {
    'PALM' : {
        "STEP" : 8,                        
        "DIR" : 10 
    },
    'DORSO' : {
        "STEP" : 16,
        "DIR" : 18
    },

}

# Speed variables
MOTOR_CONFIG = {
    "DELAY_BETWEEN_STEPS" : 0.0005, 
    "CYCLES_PER_TURN" : 200
}               

# Setup pin layout on PI
GPIO.setmode(GPIO.BOARD)

# Indicate the GPIO's usage to the board
GPIO.setup(GPIO_PINS['PALM']['STEP'], GPIO.OUT)
GPIO.setup(GPIO_PINS['PALM']['DIR'], GPIO.OUT)
GPIO.setup(GPIO_PINS['DORSO']['STEP'], GPIO.OUT)
GPIO.setup(GPIO_PINS['DORSO']['DIR'], GPIO.OUT)

# Global variable to check if there is any process happening (avoids command override and mechanical issues)
process_happening = False

# Instance the app
app = Flask(__name__)

'''
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
ENDPOINTS
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
'''
@app.route('/')
def index():
    templateData = {
        'title': 'Motor Control',
    }
    return render_template('index.html', **templateData)

# Increase or decrease N steps from the exotendon
@app.route('/step', methods=['POST'])
def step_post():
    # Parse the request's body
    data = request.get_json()

    # Obtain the number of steps and direction
    steps = data.get('steps')
    direction = data.get('direction')

    # Validate the information obtained
    if steps is None or direction is None:
        return {"error": "Missing steps or direction"}, 400

    # Perform the actual step increase
    status = set_steps(steps, direction)

    # Return a success response
    return {"status": status}, 200

'''
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
FUNCTIONS
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
'''
# Function to increase or decrease steps from the exotendon
def set_steps(steps : int, direction : str):
    # Check if there is any process happening
    global process_happening
    if (process_happening):
        return False

    # No process happening now. Rise it to avoid mechanical override
    process_happening = True

    # Set each motor's direction
    if direction == "OPEN":
        GPIO.output(GPIO_PINS['PALM']['DIR'], 0)
        GPIO.output(GPIO_PINS['DORSO']['DIR'], 1)
    else:
        GPIO.output(GPIO_PINS['PALM']['DIR'], 1)
        GPIO.output(GPIO_PINS['DORSO']['DIR'], 0)

    for x in range(steps):
        GPIO.output(GPIO_PINS['PALM']['STEP'], GPIO.HIGH)
        GPIO.output(GPIO_PINS['DORSO']['STEP'], GPIO.HIGH)
        sleep(MOTOR_CONFIG['DELAY_BETWEEN_STEPS'])

    # Stop the process and return success
    process_happening = False
    return True

'''
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
RUNTIME CONFIGURATION
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
'''
if __name__ == '__main__':
    try:
        app.run(debug=True, port=5000, host='0.0.0.0')
    finally:
        GPIO.cleanup()