import astropy.units
import numpy as np
from astropy import units as u
from numpy import cos, sin, pi


def get_2d_rotation_matrix(time: astropy.units.Quantity, rotation_period: astropy.units.Quantity) -> np.ndarray:
    """Return the matrix corresponding to a 2D rotation.
    :param time: Time variable in seconds
    :param rotation_period: Rotation period for a full rotation in seconds
    :return: An array containing the matrix
    """
    argument = 2 * pi * u.rad / rotation_period * time
    return np.array([[cos(argument), -sin(argument)],
                     [sin(argument), cos(argument)]])
