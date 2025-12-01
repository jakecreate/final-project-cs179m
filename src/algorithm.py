import numpy as np


def g_cost():
    pass


def h_cost():
    pass

def clean():
    pass


'''
Args:
    X (ndarray): m rows by n=4 cols[x, y, weight, name]

Return:
    list: contains ndarrays which contain m actions, n=2 cols[x, y]
    list: contains tuple of corresponding meta info (weight, name)

'''
def algorithm(X):
    # clean data
    # algorithm
    pass


if __name__ == '__main__':
    FOLDER_PATH = './data/'
    FILE_NAME = 'ShipCase6.txt'
    X = np.loadtxt(FOLDER_PATH+FILE_NAME, dtype=str, delimiter=',')
    X[:, 0] = np.char.strip(X[:, 0], "[")
    X[:, 1] = np.char.strip(X[:, 1], "]")
    X[:, 2] = np.char.strip(X[:, 2], "{} ")
    X[:, 3] = np.char.strip(X[:, 3], " ")
    
    algorithm(X)

