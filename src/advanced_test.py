import numpy as np
import algorithm as ag
import matplotlib.pyplot as plt
import time as ti

def file_num(num):
    return 'RowCase' + str(num) + '.txt'
FOLDER_PATH = './advanced_data/'
A_list = []
UCS_list = []
for num in range(1, 5):
    break
    FILE_NAME = file_num(num)
    X = np.loadtxt(FOLDER_PATH+FILE_NAME, dtype=str, delimiter=',')
    X[:, 0] = np.char.strip(X[:, 0], "[")
    X[:, 1] = np.char.strip(X[:, 1], "]")
    X[:, 2] = np.char.strip(X[:, 2], "{} ")
    X[:, 3] = np.char.strip(X[:, 3], " ")

    print(f'RowCase{num}.txt starting now:')
    print('----- A* -----')
    init = ti.time()
    actions, total_cost = ag.a_star(X)
    A_list.append(ti.time() - init)
    print('actions:', actions)
    print('total cost:', total_cost)

    print('----- UCS -----')
    init = ti.time()
    actions_ucs, total_cost_ucs = ag.ucs(X)
    UCS_list.append(ti.time() - init)
    print('actions_ucs:', actions_ucs)
    print('total cost:_ucs', total_cost_ucs)

# astar = np.array(A_list)
# ucs = np.array(UCS_list)

# np.savetxt('./advanced_data/astar.txt', astar)
# np.savetxt('./advanced_data/ucs.txt', ucs)
astar = np.loadtxt('./advanced_data/astar.txt')
ucs = np.loadtxt('./advanced_data/ucs.txt')

fig, ax = plt.subplots(figsize=(7, 5), dpi=500)

len_algo = np.array([2,4,6,8])
ax.plot(len_algo, astar, color='red', linewidth=3, solid_capstyle='round', label='A*')
ax.plot(len_algo, ucs, color='blue', linewidth=1, solid_capstyle='round', label='UCS')
ax.set_xticks(len_algo)
ax.set_yticks([0, 60, 120, 180])
ax.set_xlabel('N Crates')
ax.set_ylabel('Algorithm Duration (seconds)')
ax.legend()

plt.rcParams['svg.fonttype'] = 'none'
fig.savefig('./data/_test.svg', format='svg', dpi=500)

