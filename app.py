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
# ------------------------------------------------------> Constants and setup 
# Direction and step pins (palm and dorso of the hand)
GPIO_PINS = {
    'PALM' : {
        # Motor
        "STEP" : 10,                        
        "DIR" : 8,
        # Encoder
        "A" : 11,
        "B" : 13
    },
    'DORSO' : {
        # Motor
        "STEP" : 18,
        "DIR" : 16,
        # Encoder
        "A" : 19,
        "B" : 21
    },
}           

# Board configuration
# Setup pin layout on PI (use borad layout)
GPIO.setmode(GPIO.BOARD)
# Avoid warnings
GPIO.setwarnings(False)
# Motors
GPIO.setup(GPIO_PINS['PALM']['STEP'], GPIO.OUT)
GPIO.setup(GPIO_PINS['PALM']['DIR'], GPIO.OUT)
GPIO.setup(GPIO_PINS['DORSO']['STEP'], GPIO.OUT)
GPIO.setup(GPIO_PINS['DORSO']['DIR'], GPIO.OUT)
# Encoders
GPIO.setup(GPIO_PINS['PALM']['A'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_PINS['PALM']['B'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_PINS['DORSO']['A'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_PINS['DORSO']['B'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Encoder/Motor-related
MOTOR_SPEED = 0.0005
DEBOUNCE_TIME = 0.001

# ------------------------------------------------------> Global variables
# Encoder positions
ENCODERS = {
    "PALM" : {
        "LAST_A" : 0,
        "LAST_B" : 0,
        "MIN_POSITION" : 0,
        "MAX_POSITION" : 0,
        "CURRENT_POSITION" : 0
    },
    "DORSO" : {
        "LAST_A" : 0,
        "LAST_B" : 0,
        "MIN_POSITION" : 0,
        "MAX_POSITION" : 0,
        "CURRENT_POSITION" : 0
    },
}

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
    
'''
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
FUNCTIONS
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
'''
# Function to increase or decrease steps from the exotendon
def tune_post(steps : int, speed: float, direction : str, direction_override : str):    
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
        sleep(0.001)

        # Update it on every rotation
        update_position()

    # TODO: Remove
    print(ENCODERS['PALM']['CURRENT_POSITION'])
    print(ENCODERS['DORSO']['CURRENT_POSITION'])

    # Stop the process and return success
    process_happening = False
    return True

# Function to update the position of the encoders
def update_position():
    # Get the current status of the encoders
    palm_a_current, palm_b_current = GPIO.input(GPIO_PINS['PALM']['A']), GPIO.input(GPIO_PINS['PALM']['B'])
    dorso_a_current, dorso_b_current = GPIO.input(GPIO_PINS['DORSO']['A']), GPIO.input(GPIO_PINS['DORSO']['B'])

    # Update palm (only upon change)
    if palm_a_current != ENCODERS['PALM']['LAST_A'] or palm_b_current != ENCODERS['PALM']['LAST_B']:  
        # Act according to the direction of the rotation
        if palm_a_current == 1 and palm_b_current == 0 and ENCODERS['PALM']['LAST_A'] == 0:
            ENCODERS['PALM']['CURRENT_POSITION'] += 1
        elif palm_a_current == 0 and palm_b_current == 1 and ENCODERS['PALM']['LAST_B'] == 0: 
            ENCODERS['PALM']['CURRENT_POSITION'] -= 1

        # Store current state
        ENCODERS['PALM']['LAST_A'], ENCODERS['PALM']['LAST_B'] = palm_a_current, palm_b_current == 1

    # Update dorso (only upon change)
    if dorso_a_current != ENCODERS['DORSO']['LAST_A'] or dorso_b_current != ENCODERS['DORSO']['LAST_B']:  
        # Act according to the direction of the rotation
        if dorso_a_current == 1 and dorso_b_current == 0 and ENCODERS['DORSO']['LAST_A'] == 0:
            ENCODERS['DORSO']['CURRENT_POSITION'] += 1
        elif dorso_a_current == 0 and dorso_b_current == 1 and ENCODERS['DORSO']['LAST_B'] == 0: 
            ENCODERS['DORSO']['CURRENT_POSITION'] -= 1

        # Store current state
        ENCODERS['DORSO']['LAST_A'], ENCODERS['DORSO']['LAST_B'] = dorso_a_current, dorso_b_current == 1

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