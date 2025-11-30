import numpy as np
import matplotlib.pyplot as plt
import math
import time
from datetime import datetime, timedelta
import os
import sys
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)
app.config['data'] = 'data'

def call_algorithm(filename):
    FOLDER_PATH = './data/'
    X = np.loadtxt(FOLDER_PATH+filename, dtype=str, delimiter=',')
    X[:, 0] = np.char.strip(X[:, 0], "[")
    X[:, 1] = np.char.strip(X[:, 1], "]")
    X[:, 2] = np.char.strip(X[:, 2], "{} ")
    X[:, 3] = np.char.strip(X[:, 3], " ")
    # CALL THE ALGORITHM HERE
    # algorithm(X)

@app.route("/")
def index():
    return render_template("index.html")

# POST request that takes in a file in the body of the request.
# The file should have the key 'file'.
# Saves the file into the 'data' folder.
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

        # call the algorithm portion to do its thing on the info in the file
        call_algorithm(filename)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)