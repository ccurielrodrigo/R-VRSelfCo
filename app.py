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
        "STEP" : 10,                        
        "DIR" : 8 
    },
    'DORSO' : {
        "STEP" : 18,
        "DIR" : 16
    }
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

# Global variable to meassure steps from open state (0) to closed state (#)
current_status = 0
max_steps = 800

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
@app.route('/tune', methods=['POST'])
def tune_post():
    # Parse the request's body
    data = request.get_json()

    # Obtain the number of steps and direction
    steps = data.get('steps')
    direction = data.get('direction')
    direction_override = data.get('direction_override')
    speed = data.get('speed')

    # Validate the information obtained
    if steps is None or direction is None or speed is None:
        return {"error": "Missing 'steps', 'direction' or 'speed'"}, 400

    # Perform the actual step increase
    status = tune_post(steps, speed, direction, direction_override)

    # Return a success response
    return {"status": status}, 200

# Setup the open or closed state
@app.route('/setup', methods=['POST'])
def setup_post():
    # Parse the request's body
    data = request.get_json()

    # Obtain the number of steps and direction
    command = data.get('command')

    # Validate the information obtained
    if command is None:
        return {"error": "Missing 'command'"}, 400

    # Perform the actual step increase
    print (command)
    status = False

    # Return a success response
    return {"status": status}, 200

# Control for opening or closing
@app.route('/control', methods=['POST'])
def control_post():
    # Parse the request's body
    data = request.get_json()

    # Obtain the number of steps and direction
    command = data.get('command')

    # Validate the information obtained
    if command is None:
        return {"error": "Missing 'command'"}, 400

    # Perform the actual step increase
    print (command)
    status = False

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
def tune_post(steps : int, speed: float, direction : str):    
    # Check if there is any process happening
    global process_happening
    if (process_happening):
        return False

    # No process happening now. Rise it to avoid mechanical override
    process_happening = True

    # Set each motor's direction
    if direction == "OPEN":
        GPIO.output(GPIO_PINS['PALM']['DIR'], 1)
        GPIO.output(GPIO_PINS['DORSO']['DIR'], 0)
    else:
        GPIO.output(GPIO_PINS['PALM']['DIR'], 0)
        GPIO.output(GPIO_PINS['DORSO']['DIR'], 1)

    # Perform the steps
    for x in range(steps):
        # HIGH step
        if (direction_override == "NORMAL" or direction_override == "OPEN_ONLY"):
            GPIO.output(GPIO_PINS['PALM']['STEP'], GPIO.HIGH)
        if (direction_override == "NORMAL" or direction_override == "CLOSE_ONLY"):
            GPIO.output(GPIO_PINS['DORSO']['STEP'], GPIO.HIGH)
        sleep(speed)

        # LOW step
        if (direction_override == "NORMAL" or direction_override == "OPEN_ONLY"):
            GPIO.output(GPIO_PINS['PALM']['STEP'], GPIO.LOW)
        if (direction_override == "NORMAL" or direction_override == "CLOSE_ONLY"):
            GPIO.output(GPIO_PINS['DORSO']['STEP'], GPIO.LOW)
        sleep(speed)

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