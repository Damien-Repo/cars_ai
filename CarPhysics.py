#!/usr/bin/env python

import pygame
from pygame.math import Vector2 as Vec

from math import sin, radians, degrees, copysign
from CacheMath import CacheMath


class CarPhysics(object):
    IRL_CAR_LONG = 4        # in meters
    IRL_CAR_LARGE = 2       # in meters

    WIDTH = 20              # in pixels
    HEIGHT = 10             # in pixels
    HALF_WIDTH = WIDTH / 2
    HALF_HEIGHT = HEIGHT / 2

    PX_PER_UNIT = 5.        # Ratio Pixels/IRL enforced to 5

    assert WIDTH / IRL_CAR_LONG == PX_PER_UNIT
    assert HEIGHT / IRL_CAR_LARGE == PX_PER_UNIT

    MAX_ACCELERATION = 10.
    MAX_STEERING = 100.
    MAX_VELOCITY = 100.

    ACCELERATION_SPEED = 5.
    STEERING_SPEED = 100.
    BRAKE_DECELERATION_SPEED = 2 * ACCELERATION_SPEED
    FREE_DECELERATION_SPEED = ACCELERATION_SPEED / 2

    def __init__(self, start_pos: Vec, start_heading: float):
        self._front_pos = None
        self._old_pos = None

        self._start_pos = Vec(start_pos)
        self._start_heading = start_heading

        self._heading = start_heading
        self.pos = Vec(start_pos)

        self._steering = 0.
        self._acceleration = 0.
        self._velocity = Vec(0., 0.)

    def _compute_front_pos(self):
        rad = CacheMath.radians(-self._heading)
        self._front_pos = self._pos + (CacheMath.cos(-rad) * self.HALF_WIDTH, CacheMath.sin(-rad) * self.HALF_HEIGHT)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        old_pos = getattr(self, '_pos', None)

        self._pos = value
        self._compute_front_pos()

        self._old_pos = Vec(old_pos) if old_pos is not None else Vec(self._pos)

    @property
    def start_pos(self):
        return self._start_pos

    @property
    def heading(self):
        return self._heading

    @heading.setter
    def heading(self, value):
        self._heading = value
        self._compute_front_pos()

    @property
    def start_heading(self):
        return self._start_heading

    @property
    def acceleration(self):
        return self._acceleration

    @property
    def front_pos(self):
        return self._front_pos

    @staticmethod
    def _clamp(value, min_value, max_value):
        return max(min_value, min(value, max_value))

    def immobilize(self):
        self._acceleration = 0.
        self._velocity *= 0.
        self.pos = Vec(self._old_pos)

    def _move_steering(self, moves: dict, delta_time: float):
        if moves.get('right', False):
            self._steering -= self.STEERING_SPEED
        elif moves.get('left', False):
            self._steering += self.STEERING_SPEED
        else:
            self._steering = 0.0

        clamp_value = self.MAX_STEERING * delta_time
        self._steering = self._clamp(self._steering * delta_time, -clamp_value, clamp_value)

    def _move_acceleration(self, moves: dict, delta_time: float):
        def _brake():
            if abs(self._velocity.x) > delta_time * self.BRAKE_DECELERATION_SPEED:
                self._acceleration = -copysign(self.BRAKE_DECELERATION_SPEED, self._velocity.x)
            else:
                self._acceleration = -self._velocity.x / delta_time

        if moves.get('accelerate', False):
            if self._velocity.x < 0.0:
                _brake()
            else:
                self._acceleration += self.ACCELERATION_SPEED
        elif moves.get('decelerate', False):
            if self._velocity.x > 0.0:
                _brake()
            else:
                self._acceleration -= self.ACCELERATION_SPEED
        elif moves.get('brake', False):
            _brake()
        else:
            if abs(self._velocity.x) > delta_time * self.FREE_DECELERATION_SPEED:
                self._acceleration = -copysign(self.FREE_DECELERATION_SPEED, self._velocity.x)
            else:
                self._acceleration = -self._velocity.x / delta_time

        clamp_value = self.MAX_ACCELERATION * delta_time
        self._acceleration = self._clamp(self._acceleration * delta_time, -clamp_value, clamp_value)

    def move(self, moves: dict, delta_time: float):
        self._move_steering(moves, delta_time)
        self._move_acceleration(moves, delta_time)

    def update(self, delta_time):
        # self._velocity += (self._acceleration * delta_time, 0)
        self._velocity += (self._acceleration, 0)
        # print(f'velocity: {self._velocity}')

        self._velocity.x = self._clamp(self._velocity.x, -self.MAX_VELOCITY, self.MAX_VELOCITY)

        if self._steering != 0.0:
            turning_radius = self.IRL_CAR_LONG / sin(radians(self._steering))
            angular_velocity = self._velocity.x / turning_radius
        else:
            angular_velocity = 0.0

        self.heading -= degrees(angular_velocity) #* delta_time
        self.pos += self._velocity.rotate(self.heading) #* delta_time

        # print(f'pos: {self.pos}, heading: {self.heading}')
