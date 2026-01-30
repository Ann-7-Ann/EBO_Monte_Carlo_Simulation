import numpy as np

def thin_lens(f):
    return np.array([[1, 0],
                     [-1/f, 1]])

def interface(n1, n2):
    return np.array([[1, 0],
                     [0, n1/n2]])