import numpy as np

EPSILON = 1e-9


def smax(x, y, epsilon=EPSILON):
    x = np.asarray(x)
    y = np.asarray(y)
    return 0.5 * (x + y + np.sqrt((x - y) ** 2 + epsilon))


def smin(x, y, epsilon=EPSILON):
    x = np.asarray(x)
    y = np.asarray(y)
    return 0.5 * (x + y - np.sqrt((x - y) ** 2 + epsilon))


def sigmoid(z):
    z = np.asarray(z)
    return np.where(z >= 0, 1.0 / (1.0 + np.exp(-z)), np.exp(z) / (1.0 + np.exp(z)))



def dsmax_dx(x, y, epsilon=EPSILON):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 + (x - y) / np.sqrt((x - y) ** 2 + epsilon))

def dsmax_dy(x, y, epsilon=EPSILON):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 - (x - y) / np.sqrt((x - y) ** 2 + epsilon))

def dsmin_dx(x, y, epsilon=EPSILON):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 - (x - y) / np.sqrt((x - y) ** 2 + epsilon))

def dsmin_dy(x, y, epsilon=EPSILON):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 + (x - y) / np.sqrt((x - y) ** 2 + epsilon))
