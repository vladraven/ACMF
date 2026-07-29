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
    """Numerically stable sigmoid without evaluating both branches."""
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z, dtype=float)
    mask = z >= 0
    out[mask] = 1.0 / (1.0 + np.exp(-z[mask]))
    exp_z = np.exp(z[~mask])
    out[~mask] = exp_z / (1.0 + exp_z)
    return out.item() if out.shape == () else out



def dsmax_dx(x, y, epsilon=EPSILON):
    """Derivative of smax(x, y) with respect to x."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 + (x - y) / np.sqrt((x - y) ** 2 + epsilon))

def dsmax_dy(x, y, epsilon=EPSILON):
    """Derivative of smax(x, y) with respect to y."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 - (x - y) / np.sqrt((x - y) ** 2 + epsilon))

def dsmin_dx(x, y, epsilon=EPSILON):
    """Derivative of smin(x, y) with respect to x."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 - (x - y) / np.sqrt((x - y) ** 2 + epsilon))

def dsmin_dy(x, y, epsilon=EPSILON):
    """Derivative of smin(x, y) with respect to y."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return 0.5 * (1.0 + (x - y) / np.sqrt((x - y) ** 2 + epsilon))
