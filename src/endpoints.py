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
# 'move_container' = a boolean that is true if we move a container on this step and false if we're
#                    just repositioning the claw to the next cell.
# 'last_step' = a boolean that is true if we are currently on the last step and false otherwise.
ships = {}
PARK_Y_COORD = 9
PARK_X_COORD = 1

# input: none
# output: a reference to the dictionary holding all of the info for the current session.
#         This way we don't have to type ships[session['session_id']] all the time.
def get_ship():
    return ships[session['session_id']]

# input: ints y and x that are the y and x coords of a cell
# output: the index in the grid of the row that contain the info on the specified cell
def grid_index(y, x):
    y_coord = str(y)
    if y < 10:
        y_coord = '0' + y_coord

    x_coord = str(x)
    if x < 10:
        x_coord = '0' + x_coord

    X = get_ship()['grid']
    index = np.where((X[:, 0] == y_coord) & (X[:, 1] == x_coord))[0]
    return index

def call_algorithm(filename):
    FOLDER_PATH = './data/'
    X = np.loadtxt(FOLDER_PATH+filename, dtype=str, delimiter=',')

    # remove unnecessary characters
    X[:, 0] = np.char.strip(X[:, 0], "[")
    X[:, 1] = np.char.strip(X[:, 1], "]")
    X[:, 2] = np.char.strip(X[:, 2], "{} ")
    X[:, 3] = np.char.strip(X[:, 3], " ")
    X = np.hstack((X, np.array([[""] * len(X)]).T))
    ship = get_ship()
    ship['grid'] = X
    # CALL THE ALGORITHM HERE
    # steps, total_time = algorithm(X)
    
    # example data
    total_time = 10
    steps = np.array([[9, 1, 1, 2],
                      [1, 2, 2, 3],
                      [2, 3, 3, 4],
                      [3, 4, 4, 5],
                      [4, 5, 9, 1]])
    # steps = np.insert(steps, 0, [-1, -1, steps[0, 0], steps[0, 1]], axis=0)
    # steps = np.vstack((steps, [steps[-1, 2], steps[-1, 3], -1, -1]))

    ship['park'] = 'green'
    ship['steps'] = steps
    ship['num_steps'] = len(steps)
    ship['current_step_num'] = 0
    ship['total_time'] = total_time
    ship['move_container'] = False
    ship['last_step'] = False

    index = grid_index(steps[0, 2], steps[0, 3])
    ship['grid'][index, 4] = 'red'
    print(ships[session['session_id']])

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

        # redirect to the grid display page
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
    ship = get_ship()
    return jsonify(grid=ship['grid'].tolist(),
                   park_cell=ship['park'],
                   steps=ship['steps'].tolist(),
                   num_steps=ship['num_steps'],
                   current_step_num=ship['current_step_num'],
                   is_last_step=ship['last_step'])

# POST method to call when the user presses the enter key. returns the next grid step.
# Input: none
# Output: all the info you need to display the graph
#   - grid
#   - park_cell
#   - steps
#   - num_steps
#   - current_step_num
#   - is_last_step
# If you call this method and we're already on the last step, it will not advance the info
# and will just return the grid data as if you were just calling the '/api/current_grid' method
@app.route('/api/next_grid', methods = ['POST'])
def next_grid():
    ship = get_ship()
    
    # if we're already on the last step, just return the json and do nothing else
    if ship['last_step']:
        return current_grid()

    # update the manifest
    
    # append something to the log file

    # clear the color of the first cell
    curr_step = ship['current_step_num']
    first_y_coord = ship['steps'][curr_step, 0]
    first_x_coord = ship['steps'][curr_step, 1]
    if first_y_coord == PARK_Y_COORD and first_x_coord == PARK_X_COORD:
        ship['park'] = ''
    else:
        ship['grid'][grid_index(first_y_coord, first_x_coord), 4] = ''

    # clear the color of the second cell
    second_y_coord = ship['steps'][curr_step, 2]
    second_x_coord = ship['steps'][curr_step, 3]
    if second_y_coord == PARK_Y_COORD and second_x_coord == PARK_X_COORD:
        ship['park'] = ''
    else:
        ship['grid'][grid_index(second_y_coord, second_x_coord), 4] = ''

    # update 'grid'
    # if we just moved a container, update the grid by swapping the info of those cells but not the coords
    if ship['move_container']:
        first_index = grid_index(first_y_coord, first_x_coord)
        second_index = grid_index(second_y_coord, second_x_coord)
        ship['grid'][first_index, 2], ship['grid'][second_index, 2] = ship['grid'][second_index, 2], ship['grid'][first_index, 2]
        ship['grid'][first_index, 3], ship['grid'][second_index, 3] = ship['grid'][second_index, 3], ship['grid'][first_index, 3]

    # update 'current_step_num'
    ship['current_step_num'] += 1

    # update 'move_container'
    ship['move_container'] = not ship['move_container']

    # color the source cell 'green'
    new_step_num = ship['current_step_num']
    new_first_y_coord = ship['steps'][new_step_num, 0]
    new_first_x_coord = ship['steps'][new_step_num, 1]
    if new_first_y_coord == PARK_Y_COORD and new_first_x_coord == PARK_X_COORD:
        ship['park'] = 'green'
    else:
         ship['grid'][grid_index(new_first_y_coord, new_first_x_coord), 4] = 'green'

    # color the target cell 'red'
    new_second_y_coord = ship['steps'][new_step_num, 2]
    new_second_x_coord = ship['steps'][new_step_num, 3]
    if new_second_y_coord == PARK_Y_COORD and new_second_x_coord == PARK_X_COORD:
        ship['park'] = 'red'
    else:
         ship['grid'][grid_index(new_second_y_coord, new_second_x_coord), 4] = 'red'

    # if this is the last step, flip the boolean to indicate so
    if ship['current_step_num'] == ship['num_steps'] - 1:
        ship['last_step'] = True

    return current_grid()

if __name__ == '__main__':
    app.run(debug=True)