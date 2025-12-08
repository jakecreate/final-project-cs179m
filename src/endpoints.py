import numpy as np
import matplotlib.pyplot as plt
# import math
import time
from datetime import datetime
import os
# import sys
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, abort, session, jsonify, send_file
import secrets
import algorithm
import shutil

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
# 'all_done' = a boolean that is true if we are currently on the last step and false otherwise.
# 'file_name' = the full path of the file that contains the outbound manifest.
# 'output_name' = the name that the file should be when we output it.
# 'total_time' = the total time all of the steps will take not including the steps to and from the park cell.
ships = {}
PARK_Y_COORD = 9
PARK_X_COORD = 1
LOG_FILE_NAME = ''

def log_header():
    time = datetime.now()
    def extend(int):
        output = str(int)
        if int < 10:
            output = '0' + output
        return output
    return extend(time.month) + " " + extend(time.day) + " " + str(time.year) + ": " + extend(time.hour) + ":" + extend(time.minute) + " "

def log(str):
    with open(LOG_FILE_NAME, "a") as file:
        file.write(log_header() + str + "\n")

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
    return index[0]

def get_unique_file_name(folder_path, file_name):
    counter = 0
    original = file_name.split(".")[0]
    extension = "." + file_name.split(".")[1]
    while os.path.exists(folder_path + file_name):
        counter += 1
        file_name = original + str(counter) + extension
    return file_name

# formats the data, runs the algorithm, and fills the dictionary
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

    # log the file opening
    num_containers = len(np.where((X[:, 3] != 'NAN') & (X[:, 3] != 'UNUSED'))[0])
    ending = ''
    if num_containers != 1:
        ending = " containers on the ship."
    else:
        ending = " container on the ship."
    log("Manifest " + filename + " is opened, there are " + str(num_containers) + ending)

    steps, total_time = algorithm.a_star(X)

    # log that we found a solution
    moves = ''
    if len(steps) != 1:
        moves = " moves"
    else:
        moves = " move"
    minutes = ''
    if total_time != 1:
        minutes = " minutes"
    else:
        minutes = " minute"
    log("Balance solution found, it will require " + str(len(steps)) + moves + "/" + str(total_time) + minutes + ".")

    # rename the file to "file_nameOUTBOUND.txt"
    output_name = filename.split(".")[0]+"OUTBOUND.txt"
    full_name = FOLDER_PATH + get_unique_file_name(FOLDER_PATH, output_name)
    
    shutil.copyfile(FOLDER_PATH + filename, full_name)

    ship['file_name'] = full_name
    ship['output_name'] = output_name

    # if there are no steps to take, that means the ship is already balanced
    already_balanced = len(steps) == 0

    # if the ship is already balanced, don't add the movements for going
    # to and from the park cell
    if not already_balanced:
        steps = np.insert(steps, 0, [9, 1, steps[0, 0], steps[0, 1]], axis=0)
        steps = np.vstack((steps, [steps[-1, 2], steps[-1, 3], 9, 1]))

    # if the ships is already balanced, we don't have to display any steps
    if not already_balanced:
        ship['park'] = 'green'
    else:
        ship['park'] = ''

    ship['steps'] = steps
    ship['num_steps'] = len(steps)
    ship['current_step_num'] = 0
    ship['total_time'] = total_time
    ship['move_container'] = False
    ship['all_done'] = already_balanced

    if not already_balanced:
        index = grid_index(steps[0, 2], steps[0, 3])
        ship['grid'][index, 4] = 'red'

def unique_token():
    while True:
        # Use the number 16 since it's what most encryption services use
        # so it must be pretty good.
        token = secrets.token_urlsafe(16)
        if token not in ships:
            return token

# GET method that just redirects you to to start.html
# If it is the first time the window was opened, start a log file.
@app.route("/")
def display_start():
    global LOG_FILE_NAME
    # if we haven't given it a 'first_log' entry yet
    # this means it's the first time on the page for this session
    if 'first_log' not in session:
        time = datetime.now()
        def extend(int):
            output = str(int)
            if int < 10:
                output = '0' + output
            return output
        file_name = "KeoghsPort" + extend(time.month) + "_" + extend(time.day) + "_" + str(time.year) + "_" + extend(time.hour) + extend(time.minute) + ".txt"
        path = './logs/'
        LOG_FILE_NAME = path + file_name

        # if a file already exists with that name, delete the old file
        if os.path.exists(LOG_FILE_NAME):
            os.remove(LOG_FILE_NAME)

        with open(LOG_FILE_NAME, "a") as file:
            file.write(log_header() + "Window was opened.\n")
        session['first_log'] = False
    return render_template("start.html")

# POST request that takes in a file in the body of the request.
# The file should have the key 'file'.
# Saves the file into the 'data' folder.
# Redirects to the grid page if the file exists.
@app.route('/', methods = ['POST'])
def upload():
    # get the file with the 'file' key from the request
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
        uploaded_file.close()

        # Flask manages an array session[] for us but it lives in the browser
        # cookies so the amount of storage isn't enough for our large grid.
        # To fix this, we use our own dictionary to store info.
        # V stores a session_id in the browser cookies
        session['session_id'] = unique_token()
        ships[session['session_id']] = {}

        # call the algorithm portion to do its thing on the info in the file
        call_algorithm(filename)

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
    temp_steps = []
    if len(ship['steps']) != 0:
        temp_steps = ship['steps'].tolist()
    return jsonify(grid=ship['grid'].tolist(),
                   park_cell=ship['park'],
                   steps=temp_steps,
                   num_steps=ship['num_steps'],
                   current_step_num=ship['current_step_num'],
                   all_done=ship['all_done'],
                   total_time=int(ship['total_time']))

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
    if ship['all_done']:
        return current_grid()

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

    # if we just finished the last step, we'll clear the colors and flip to 'all_done'
    # bool to indicate that we're done. We will not change anything else.
    if ship['current_step_num'] >= ship['num_steps'] - 1:
        ship['all_done'] = True
        return current_grid()

    # if we moved a container this step, update 'grid' and the manifest
    if ship['move_container']:
        first_index = grid_index(first_y_coord, first_x_coord)
        second_index = grid_index(second_y_coord, second_x_coord)

        # update the manifest
        # get a list of the lines in the file
        file = []
        with open(ship['file_name'], "r") as r:
            file = r.readlines()
    
        # rewrite the specific lines
        def to_formatted_string(line):
            return "[" + line[0] + "," + line[1] + "], {" + line[2] + "}, " + line[3] + "\n"
        
        # create a copy of the lines to be swapped
        line1 = ship['grid'][first_index].copy()
        line2 = ship['grid'][second_index].copy()

        # swap the data but not the coordinates
        line1[2], line2[2] = line2[2], line1[2]
        line1[3], line2[3] = line2[3], line1[3]

        # write the new lines to the list 'file'
        file[first_index] = to_formatted_string(line1)
        file[second_index] = to_formatted_string(line2)

        # write it to the file
        with open(ship['file_name'], "w") as w:
            w.writelines(file)

        # update the 'grid' in the same way
        ship['grid'][first_index, 2], ship['grid'][second_index, 2] = ship['grid'][second_index, 2], ship['grid'][first_index, 2]
        ship['grid'][first_index, 3], ship['grid'][second_index, 3] = ship['grid'][second_index, 3], ship['grid'][first_index, 3]

        # log that we moved a container
        def to_string(num):
            output = str(num)
            if num < 10:
                output = '0' + output
            return output
        coords = ship['steps'][curr_step]
        log("[" + to_string(coords[0]) + "," + to_string(coords[1]) + "] was moved to [" + to_string(coords[2]) + "," + to_string(coords[3]) + "]")

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

    return current_grid()

# input: none
# output: the new manifest will be downloaded into the user's downloads folder
@app.route('/download_manifest')
def download_manifest():
    ship = get_ship()

    # log the output
    log("Finished a Cycle. Manifest " + ship['output_name'] + " was written to desktop, and a reminder pop-up to operator to send file was displayed.")
    
    # output the file
    current_directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_directory, '..', 'data', ship['file_name'].split("/")[-1])
    full_path = os.path.normpath(path)
    return send_file(full_path, as_attachment = True, download_name = ship['output_name'])

# input: what the user wants to log
# output: redirects back to the page you were already one
@app.route('/log', methods = ['POST'])
def log_message():
    message = request.form.get('message')
    log(message)
    return redirect(request.referrer or url_for('display_start'))

# input: none
# output: the log files will be downloaded into the user's downloads folder
@app.route('/close')
def close():
    log("Log file was downloaded.")

    ship = get_ship()
    current_directory = os.path.dirname(os.path.abspath(__file__))
    plain_name = LOG_FILE_NAME.split("/")[-1]
    path = os.path.join(current_directory, '..', 'logs', plain_name)
    full_path = os.path.normpath(path)
    return send_file(full_path, as_attachment = True, download_name = plain_name)

if __name__ == '__main__':
    app.run(debug=True)