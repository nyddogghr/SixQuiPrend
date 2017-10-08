from flask import render_template
from sixquiprend.sixquiprend import app

@app.route('/')
def get_index():
    return render_template('index.html')

@app.route('/partial/<path:path>')
def get_partial_template(path):
    return render_template('/partial/{}'.format(path))
