import numpy as np
from queue import PriorityQueue

def imbalance_score(w):
    mask = w[:, 1] <= 6
    return abs(np.sum(w[mask, 2]) - np.sum(w[~mask, 2]))    


def heuristic():
    pass


def neighbors():
    pass


class Node:

    def __init__(self, w: np.ndarray, label: np.ndarray, action: np.ndarray, parent: object):
        self.w = w # 96 by 3 where cols= y, x, weight --> represent 8 x 12 grid
        self.label = label # vector length 96 --> represent each label on 8 x12 grid
        self.action = action # vector of [y1, x1, y2, x2]
        self.parent = parent # the node in which it came from 
        if action is not None: self.cost = abs(action[0] - action[2]) + abs(action[1] + action[3]) # cost of action to get to this node
        self.score = imbalance_score(w)
        

    def __eq__(self, other: object):
        return np.array.equal(self.w, other.w) and np.array.equal(self.label == other.label)

    
    def __hash__(self):
        self.w.flags.writeable = False
        self.label.flags.writeable = False
        return hash((self.w.tobytes(), self.label.tobytes()))


def a_star(X : np.ndarray):
    # ds & init
    open = PriorityQueue()
    opened = set()
    closed = set()

    start = Node(np.int64(X[:, 0:3]), X[:, 3], None, None) 
    open.put((0, start))
    opened.add(start)
    # set goal
    min_local = round(np.sum(start.w[:, 2])*0.10, 2)
    min_global = np.diff(np.sort(start.w[:, 2])[0:2]).item() if X.shape[0] % 2 == 0 else np.min(start.w[:, 2]).item()

    print(min_local, min_global)
    print(len(opened))

    while not open.empty():

        fn, node = open.get()
        if (node.score <= min_global) or (node.score <= min_local):
            print('hello')
        break


if __name__ == '__main__':
    FOLDER_PATH = './data/'
    FILE_NAME = 'ShipCase6.txt'
    X = np.loadtxt(FOLDER_PATH+FILE_NAME, dtype=str, delimiter=',')
    X[:, 0] = np.char.strip(X[:, 0], "[")
    X[:, 1] = np.char.strip(X[:, 1], "]")
    X[:, 2] = np.char.strip(X[:, 2], "{} ")
    X[:, 3] = np.char.strip(X[:, 3], " ")

    a_star(X)


