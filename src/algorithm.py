import numpy as np
from queue import PriorityQueue

def imbalance_score(w):
    mask = w[:, 1] <= 6
    return abs(np.sum(w[mask, 2]) - np.sum(w[~mask, 2]))    


def heuristic(target_weight: int, node: object):
    '''
    goal: find minimum number of crates it takes to fill up the lesser side to the target_weight
    '''
    w_mask = (node.label != 'UNUSED') & (node.label != 'NAN')
    p_mask = node.w[:, 1] <= 6

    # weights of each side P & S
    p_weights = node.w[p_mask & w_mask, 2]
    s_weights = node.w[~p_mask & w_mask, 2]

    # each side total weight - ideal weight
    p_diff = np.sum(p_weights) - target_weight
    s_diff = np.sum(s_weights) - target_weight

    # picking which side receives weights
    smaller_diff = None
    bigger_weights = None
    if p_diff <= s_diff: # heaviver side is S, moving to P
        smaller_diff = abs(p_diff)
        bigger_weights = s_weights
    else:
        smaller_diff = abs(s_diff)
        bigger_weights = p_weights

    # algorithm
    sum_weight = 0 # to get to at least diff or greater
    sum_count = 0
    while sum_weight < smaller_diff:
        # pick weight that fills nearly the same about as smaller difference from current to target weight
        idx = np.argmin(np.abs(bigger_weights - smaller_diff))
        weight = bigger_weights[idx]

        sum_weight+=weight
        sum_count+=1
        # remove weight from heavier side
        bigger_weights = np.delete(bigger_weights, idx, axis=0)
    
    return sum_count

# return possible neighbors of node
def neighbors(node: object):
    is_crate = (node.label != 'UNUSED') & (node.label != 'NAN')       
    is_avail = (node.label != 'NAN') & ~is_crate

    idx_top_avail_list = []
    idx_top_crates_list = []
    # in each col
    for col in range(1, 13):
        is_col = node.w[:, 1] == col
        idx_crates = (is_col & is_crate).nonzero()[0] # idx of each crate
        idx_top_avail = (is_col & is_avail).nonzero()[0]# idx of available spot
        
        if idx_crates.size != 0:
            idx_top_crates_list.append(idx_crates[-1])
        if idx_top_avail.size !=0:
            idx_top_avail_list.append(idx_top_avail[0])
    
    top_avail = np.vstack(idx_top_avail_list).ravel()
    top_crates = np.vstack(idx_top_crates_list).ravel()

    print('top_avail:', top_avail)
    print('top_crates:', top_crates)
    neighbors_list = []
    for idx_crate in top_crates:
        crate = node.w[idx_crate]
        col_num = crate[1]
        for idx_spot in np.delete(top_avail, col_num - 1):
            spot = node.w[idx_spot]
            # create attributes
            action = np.array([crate[0], crate[1], spot[0], spot[1]])
            w = node.w.copy()
            label = node.label.copy()
            # swap
            w[[idx_crate, idx_spot]] = w[[idx_spot, idx_crate]]
            label[[idx_crate, idx_spot]] = label[[idx_spot, idx_crate]]
           
            neighbors_list.append(Node(w, label, action, node))
        
    return neighbors_list # consider adding top limit 


class Node:
    def __init__(self, w: np.ndarray, label: np.ndarray, action: np.ndarray, parent: object):
        self.w = w # 96 by 3 where cols= y, x, weight --> represent 8 x 12 grid
        self.label = label # vector length 96 --> represent each label on 8 x12 grid
        self.action = action # vector of [y1, x1, y2, x2]
        self.parent = parent # the node in which it came from 
        self.cost = abs(action[0] - action[2]) + abs(action[1] + action[3]) if action is not None else 0 # cost of action to get to this node
        self.gn = parent.gn + self.cost if parent is not None else self.cost
        self.hn = heuristic(np.sum(w[:, 2])/2, self)
        self.score = imbalance_score(w)


    def __eq__(self, other: object):
        return np.array.equal(self.w, other.w) and np.array.equal(self.label, other.label)

    
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
    total_weight = np.sum(start.w[:, 2])
    target_weight = total_weight/2

    min_local = round(total_weight*0.10, 2)
    min_global = np.diff(np.unique(np.sort(start.w[:, 2]))[0:2]).item() if X.shape[0] % 2 == 0 else np.min(start.w[:, 2]).item()

    while not open.empty():

        fn, node = open.get()
        print(node.hn)
        if (node.score <= min_global) or (node.score <= min_local): break
        closed.add(node)
        
        for neighbor in neighbors(node):
            break
        
        break
        

if __name__ == '__main__':
    FOLDER_PATH = './data/'
    FILE_NAME = 'ShipCase4.txt'
    X = np.loadtxt(FOLDER_PATH+FILE_NAME, dtype=str, delimiter=',')
    X[:, 0] = np.char.strip(X[:, 0], "[")
    X[:, 1] = np.char.strip(X[:, 1], "]")
    X[:, 2] = np.char.strip(X[:, 2], "{} ")
    X[:, 3] = np.char.strip(X[:, 3], " ")

    a_star(X)


