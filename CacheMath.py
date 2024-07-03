
from numba import jit
import math

class CacheMath(object):
    _RAD = {}
    _COS = {}
    _SIN = {}

    @staticmethod
    def _get_value(angle, func, cache):
        if angle not in cache:
            cache[angle] = func(angle)
        return cache[angle]

    @staticmethod
    @jit(fastmath=True)
    def _radians(angle):
        return math.radians(angle)

    @staticmethod
    @jit(fastmath=True)
    def _cos(angle):
        return math.cos(angle)

    @staticmethod
    @jit(fastmath=True)
    def _sin(angle):
        return math.sin(angle)

    @staticmethod
    def radians(angle):
        return CacheMath._get_value(angle, CacheMath._radians, CacheMath._RAD)

    @staticmethod
    def cos(angle):
        return CacheMath._get_value(angle, CacheMath._cos, CacheMath._COS)

    @staticmethod
    def sin(angle):
        return CacheMath._get_value(angle, CacheMath._sin, CacheMath._SIN)
