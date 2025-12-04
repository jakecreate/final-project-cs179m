import numpy as np
import matplotlib.pyplot as plt
import math
import time
from datetime import datetime, timedelta
import os
import sys
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify
import secrets

app = Flask(__name__)
app.config['data'] = 'data'
app.secret_key = secrets.token_hex()

# This dictionary will store all of the data for all of the different sessions.
# The key is the session_id found in the session array managed by Flask.
# The value is an dictionary containing several things
# 'grid' = an array of the entire ship at step n. ship[x] = (y_coord, x_coord, container_weight, container_name)
# 'park' = a string that is either 'blank', 'green', or 'red' indicating what color the park cell should be at the current step.
# 'steps' = an nparray of steps we have to take. steps[n - 1] = (old_y_coord, old_x_coord, new_y_coord, new_x_coord)
#           where n is the step we're currently on.
# 'num_steps' = total number of steps.
# 'current_step_num' = a counter to track what step we are currently on. Initialized to 0 so that it syncs with the array 'steps'
ships = {}

def call_algorithm(filename):
    FOLDER_PATH = './data/'
    X = np.loadtxt(FOLDER_PATH+filename, dtype=str, delimiter=',')

    # remove unnecessary characters
    X[:, 0] = np.char.strip(X[:, 0], "[")
    X[:, 1] = np.char.strip(X[:, 1], "]")
    X[:, 2] = np.char.strip(X[:, 2], "{} ")
    X[:, 3] = np.char.strip(X[:, 3], " ")

    # CALL THE ALGORITHM HERE
    # steps, total_time = algorithm(X)
    
    # example data
    total_time = 10
    steps = np.array([[1, 2, 3, 4],
                      [2, 3, 4, 5]])
    steps = np.insert(steps, 0, [-1, -1, steps[0, 0], steps[0, 1]], axis=0)
    steps = np.vstack((steps, [steps[-1, 2], steps[-1, 3], -1, -1]))

    # add an extra column to specify color
    X = np.hstack((X, np.array([[""] * len(X)]).T))

    # initialize all of the info needed to display the grid
    ships[session['session_id']]['grid'] = X
    ships[session['session_id']]['park'] = 'green'
    ships[session['session_id']]['steps'] = steps
    ships[session['session_id']]['num_steps'] = len(steps)
    ships[session['session_id']]['current_step_num'] = 0
    ships[session['session_id']]['total_time'] = total_time
    
    # turn y into a string. prepend a 0 if needed
    y = steps[0, 2]
    y_coord = str(y)
    if y < 10:
        y_coord = '0' + y_coord

    # turn x into a string. prepend a 0 if needed
    x = steps[0, 3]
    x_coord = str(x)
    if x < 10:
        x_coord = '0' + x_coord

    # get the row number that specifies the target cell
    index = np.where((X[:, 0] == y_coord) & (X[:, 1] == x_coord))[0]

    # set its color to 'red'
    ships[session['session_id']]['grid'][index, 4] = 'red'

def unique_token():
    while True:
        # Use the number 16 since it's what most encryption services use
        # so it must be pretty good.
        token = secrets.token_urlsafe(16)
        if token not in ships:
            return token

# GET method that just redirects you to to start.html
@app.route("/")
def display_start():
    return render_template("start.html")

# POST request that takes in a file in the body of the request.
# The file should have the key 'file'.
# Saves the file into the 'data' folder.
# Redirects to the grid page if the file exists.
@app.route('/', methods = ['POST'])
def upload():
    # get the file with the 'file' key from the request
    # a = np.array([[""] * 96])
    # print(a)
    uploaded_file = request.files['file']

    # if there is a file, handle it
    if uploaded_file.filename != '':
        
        # secure the filename incase it's a dangerous name
        filename = secure_filename(uploaded_file.filename)

        # if it's not a .txt file, throw an error 400 Bad Request
        if filename.split('.')[1] != "txt":
            abort(400)
            return "", 400
        
        # upload the file to the 'data' folder
        uploaded_file.save(os.path.join(app.config['data'], filename))

        # Flask manages an array session[] for us but it lives in the browser
        # cookies so the amount of storage isn't enough for our large grid.
        # To fix this, we use our own dictionary to store info.
        # V stores a session_id in the browser cookies
        session['session_id'] = unique_token()
        ships[session['session_id']] = {}

        # call the algorithm portion to do its thing on the info in the file
        call_algorithm(filename)

        # also return the grid at the current step (which is step 1), the total number of steps, the current step

        # display the grid
        return redirect(url_for('display_grid'))
    
    # if a file doesn't exist, redirect to the start page
    return redirect(url_for('display_start'))

# GET method that just redirects you to to grid.html
@app.route("/grid")
def display_grid():
    return render_template("grid.html")

# GET method that returns a json containing all the info needed to display the grid.
# This will be the information for the current step, not the next step.
# Any method that starts with '/api' returns a json
@app.route('/api/current_grid', methods = ['GET'])
def current_grid():
    return jsonify(grid=ships[session['session_id']]['grid'].tolist(),
                   park_cell=ships[session['session_id']]['park'],
                   steps=ships[session['session_id']]['steps'].tolist(),
                   num_steps=ships[session['session_id']]['num_steps'],
                   current_step_num=ships[session['session_id']]['current_step_num'])

# POST method to call when the user presses the enter key. returns the next grid step.
# No input needed.
# Output, a grid object containing the grid to display, the step we're on, the total number of steps.
@app.route('/api/next_grid', methods = ['POST'])
def next_grid():
    pass

if __name__ == '__main__':
    app.run(debug=True)