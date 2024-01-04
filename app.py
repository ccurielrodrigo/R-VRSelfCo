# Imports
from flask import Flask, render_template
import datetime

# Instance the app
app = Flask(__name__)

# Endpoints
@app.route('/')
def index():
	now = datetime.datetime.now()
	timeString = now.strftime("%Y-%m-%d %H:%M")
	templateData = {
      		'title' : 'HELLO!',
      		'time': timeString
      	}
	return render_template('index.html', **templateData)

# Runtime configuration
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
