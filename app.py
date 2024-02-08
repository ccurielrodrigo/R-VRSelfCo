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
    'BUZZER' : 32
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
# Buzzer
GPIO.setup(GPIO_PINS['BUZZER'], GPIO.OUT)

# Encoder/Motor-related
DEBOUNCE_TIME = 0.001
DEFAULT_SPEED = 0.0005
BUZZ_TIME = 5

# ------------------------------------------------------> Global variables
# Encoder positions
ENCODERS = {
    "PALM" : {
        "LAST_A" : 0,
        "LAST_B" : 0,
        "MAX_POSITION" : 0,
        "CURRENT_POSITION" : 0
    },
    "DORSO" : {
        "LAST_A" : 0,
        "LAST_B" : 0,
        "MAX_POSITION" : 0,
        "CURRENT_POSITION" : 0
    },
}

# Global variable to check if there is any process happening (avoids command override and mechanical issues)
process_happening = False

# Buzzer
buzzer = GPIO.PWM(GPIO_PINS['BUZZER'], 100)  # 100 Hz is a good frequency for a beep sound

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

# Increase or decrease N steps from the exotendon
@app.route('/setup', methods=['POST'])
def setup():
    # Parse the request's body
    data = request.get_json()

    print (data)

    # Obtain the number of steps and direction
    setup_type = data.get('setup_type')

    # Validate the information obtained
    if setup_type is None:
        return {"error": "Missing 'setup_type'"}, 400

    # Perform the actual step increase
    status = setup_limit(setup_type)

    # Return a success response
    return {"status": status}, 200

# Set the exotendon to a limit position (opened or closed)
@app.route('/control', methods=['POST'])
def control():
    # Parse the request's body
    data = request.get_json()

    # Obtain the number of steps and direction
    command = data.get('command')

    # Validate the information obtained
    if command is None:
        return {"error": "Missing 'command'"}, 400

    # Perform the actual step increase
    status = setup_control(command)
    buzz_alert(BUZZ_TIME)

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
        sleep(DEBOUNCE_TIME)

        # Update it on every rotation
        update_position()

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

# Function for defining the closed or open position of the exotendon
def setup_limit (setup_type : str):
    # Check if there is any process happening
    global process_happening
    if (process_happening):
        return False

    # No process happening now. Rise it to avoid mechanical override
    process_happening = True

    # Set each motor's direction
    if setup_type == "SET_OPEN":
        # Indicate this position as the lowest end (set to 0)
        ENCODERS['DORSO']['CURRENT_POSITION'] = 0
        ENCODERS['PALM']['CURRENT_POSITION'] = 0

        # Print a signal of success
        print("Open position successfully configured")
        print("Palm information")
        print(f"   - CURRENT_POSITION {ENCODERS['PALM']['CURRENT_POSITION']}")
        print(f"   - MAX_POSITION {ENCODERS['PALM']['MAX_POSITION']}")

        print("Dorso information")
        print(f"   - CURRENT_POSITION {ENCODERS['PALM']['CURRENT_POSITION']}")
        print(f"   - MAX_POSITION {ENCODERS['PALM']['MAX_POSITION']}")

    else:
        # Indicate this position as the highest possible
        ENCODERS['DORSO']['MAX_POSITION'] = ENCODERS['DORSO']['CURRENT_POSITION']
        ENCODERS['PALM']['MAX_POSITION'] = ENCODERS['PALM']['CURRENT_POSITION']
        
        # Print a signal of success
        print("Closed position successfully configured")
        print("Palm information")
        print(f"   - CURRENT_POSITION {ENCODERS['PALM']['CURRENT_POSITION']}")
        print(f"   - MAX_POSITION {ENCODERS['PALM']['MAX_POSITION']}")

        print("Dorso information")
        print(f"   - CURRENT_POSITION {ENCODERS['PALM']['CURRENT_POSITION']}")
        print(f"   - MAX_POSITION {ENCODERS['PALM']['MAX_POSITION']}")


    # Stop the process and return success
    process_happening = False
    return True

# Produce a given position on the exotendon
def setup_control( command : str ): 
    # Check if there is any process happening
    global process_happening
    if (process_happening):
        return False

    # No process happening now. Rise it to avoid mechanical override
    process_happening = True

    # Set each motor's direction
    if command == "OPEN":
        GPIO.output(GPIO_PINS['PALM']['DIR'], 1)
        GPIO.output(GPIO_PINS['DORSO']['DIR'], 0)
    else:
        GPIO.output(GPIO_PINS['PALM']['DIR'], 0)
        GPIO.output(GPIO_PINS['DORSO']['DIR'], 1)

    # Perform as much steps as required untill the condition is met
    global_condition_met = False
    palm_condition_met = False
    dorso_condition_met = False

    while not global_condition_met:
        # Check for individual requirements of the dorso and palm sensors
        if ((command == "CLOSE" and ENCODERS['DORSO']['CURRENT_POSITION'] <= ENCODERS['DORSO']['MAX_POSITION']) or (command == "OPEN" and ENCODERS['DORSO']['CURRENT_POSITION'] >= 0)):
            dorso_condition_met = True
        if ((command == "CLOSE" and ENCODERS['PALM']['CURRENT_POSITION'] <= ENCODERS['PALM']['MAX_POSITION']) or (command == "OPEN" and ENCODERS['PALM']['CURRENT_POSITION'] >= 0)):
            palm_condition_met = True

        # HIGH step
        if (not palm_condition_met):
            GPIO.output(GPIO_PINS['PALM']['STEP'], GPIO.HIGH)
        if (not dorso_condition_met):
            GPIO.output(GPIO_PINS['DORSO']['STEP'], GPIO.HIGH)
        sleep(DEFAULT_SPEED)

        # LOW step
        if (not palm_condition_met):
            GPIO.output(GPIO_PINS['PALM']['STEP'], GPIO.LOW)
        if (not dorso_condition_met):
            GPIO.output(GPIO_PINS['DORSO']['STEP'], GPIO.LOW)
        sleep(DEBOUNCE_TIME)

        # Update it on every rotation
        update_position()

        # Check if the condition has been met
        if (dorso_condition_met and palm_condition_met):
            global_condition_met = True

    print (f"Command {command} finished")

    # Stop the process and return success
    process_happening = False
    return True

# Generate an auditory alert for starting and ending processes
def buzz_alert(time_to_buzz: float):
    # Start the PWM
    buzzer.start(0)
    
    # Keep the beep on for the specified duration
    for dc in range(0, 101, 10):
        buzzer.ChangeDutyCycle(dc)
        sleep(0.1)
    
    # Stop the PWM
    buzzer.stop()

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