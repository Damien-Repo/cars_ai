
import pygame
import pygame.gfxdraw

from pygame.math import Vector2 as Vec

import numpy as np

import config

from Controls import Controls

from Sensors import Sensors
from CarPhysics import CarPhysics
from CacheMath import CacheMath

class MyCarPhysics(object):

    ACCELERATION_FORCE = .5
    BRAKE_FORCE = -2.

    ROTATION_FORCE = 5.

    MAX_ACCELERATION = 5.

    def __init__(self, start_pos, start_heading):
        self._front_pos = None

        self._start_pos = Vec(start_pos)
        self._start_heading = start_heading

        self._heading = start_heading
        self.pos = Vec(start_pos)

        self._old_pos = Vec(self.pos)

        self._steering = 0.
        self._acceleration = 0.
        self._vel = Vec()

    def _compute_front_pos(self):
        rad = CacheMath.radians(-self._heading)
        self._front_pos = self._pos + (CacheMath.cos(-rad) * Car.CAR_HW, CacheMath.sin(-rad) * Car.CAR_HW)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        self._compute_front_pos()

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

    def move(self, left=False, right=False, accelerate=False, brake=False):
        if left:
            self._heading += -self.ROTATION_FORCE
        if right:
            self._heading += self.ROTATION_FORCE

        if accelerate:
            self._acceleration += self.ACCELERATION_FORCE
        if brake:
            self._acceleration += self.BRAKE_FORCE

        if self._acceleration < self.ACCELERATION_FORCE:
            self._acceleration = 0.
        if self._acceleration > self.MAX_ACCELERATION:
            self._acceleration = self.MAX_ACCELERATION

        vel = Vec(1, 0).rotate(self._heading)
        vel *= self._acceleration

        self._old_pos = Vec(self.pos)
        self.pos += vel

    def update(self, game_map):
        if not game_map.point_is_on_path(self.front_pos):
            self._acceleration = 0.
            self.pos = Vec(self._old_pos)
            return

        self._acceleration *= .99


class Car(Controls):

    __CONTROLS__ = {
        config.KEYS.GAME.DEBUG.BEST_ONLY: 'Toggle drawing best only',
    }
    __CONTROLS_SUBCLASSES__ = [ Sensors ]

    _img_best = pygame.image.load('imgs/best_car.png')
    _img_std = pygame.image.load('imgs/car.png')

    _is_drawing_best_only = False

    CAR_W, CAR_H = _img_std.get_size()
    CAR_HW, CAR_HH = CAR_W / 2, CAR_H / 2

    def __init__(self, start_pos, start_heading, map_gen, stonemiles_count_max):
        self._map_gen = map_gen
        self._stonemiles_count_max = stonemiles_count_max

        self._body = CarPhysics(start_pos, start_heading)
        self._sensors = Sensors(self._body)

        self._is_alive = True
        self.is_best = False

        self._cur_stonemile = -1
        self._old_stonemile = -1
        self._stonemiles_count = 0
        self._laps_count = 0

        self._is_wrong_way = False

        self._cur_actions = {}

        self.reset()

    def reset(self):
        self._is_alive = True
        self.is_best = False

        self._cur_stonemile = -1
        self._old_stonemile = -1
        self._stonemiles_count = 0
        self._laps_count = 0

        self._is_wrong_way = False

    @property
    def pos(self):
        return self._body.pos

    def dead(self):
        self._is_alive = False

    @property
    def is_dead(self):
        return not self._is_alive

    @staticmethod
    def should_be_alive(func):
        def wrapper_func(self, *args, **kwargs):
            if self.is_dead:
                return
            func(self, *args, **kwargs)
        return wrapper_func

    @property
    def laps_count(self):
        return self._laps_count

    @classmethod
    def event(cls, event):
        if event.type == pygame.KEYDOWN:
            # Debug controls
            if cls.is_event_control(event, config.KEYS.GAME.DEBUG.BEST_ONLY):
                cls._is_drawing_best_only = not cls._is_drawing_best_only

        Sensors.event(event)

    def _get_move_actions(self):
        raise NotImplementedError

    def _move(self, delta_time):
        self._cur_actions = self._get_move_actions()
        self._body.move(self._cur_actions, delta_time)

    def is_lap_end(self):
        if self._old_stonemile == self._stonemiles_count_max - 1 and \
            self._cur_stonemile == 0:
            return True

        return False

    def _detect_inner_map(self, game_map):
        if not game_map.point_is_on_path(self._body.front_pos):
            #print(f'collision')
            self.dead()
            return

    def _detect_wrong_way(self, _):
        if self._old_stonemile == -1 or \
            self._cur_stonemile == -1:
            return

        if self.is_lap_end():
            return

        if self._cur_stonemile - self._old_stonemile < 0:
            print(f'wrong way: {self._cur_stonemile} - {self._old_stonemile} < 0')
            self.dead()
            self._is_wrong_way = True

    def _detect_lap_end(self, _):
        if not self.is_lap_end():
            return

        print(f'## End of lap {self._laps_count} ##')

        self._stonemiles_count += 1
        self._laps_count += 1

    @should_be_alive
    def update_prolog(self, game_map):
        self._cur_stonemile = -1

        if game_map.point_is_on_path(self._body.front_pos):
            path_point = game_map.get_path_point(self._body.front_pos)
            if path_point is not None:
                _, self._cur_stonemile = path_point

        self._sensors.update_prolog(game_map)

    @should_be_alive
    def update_move(self, delta_time):
        # Move the car
        self._move(delta_time)

    @should_be_alive
    def update_detection(self, game_map):
        # Detection
        detections = [
            '_detect_inner_map',
            '_detect_wrong_way',
            '_detect_lap_end',
        ]
        for detect_func in detections:
            assert hasattr(self, detect_func)
            if self.is_dead:
                return
            getattr(self, detect_func)(game_map)

    @should_be_alive
    def update_epilog(self, game_map, delta_time):
        # Update physics
        self._body.update(delta_time)
        if not game_map.point_is_on_path(self._body.front_pos):
            self._body.immobilize()

        if self._old_stonemile < self._cur_stonemile:
            self._stonemiles_count += 1

        self._old_stonemile = self._cur_stonemile

        self._sensors.update_epilog(game_map)

    @should_be_alive
    def update(self, game_map, delta_time):
        self.update_prolog(game_map)
        self.update_move(delta_time)
        self.update_detection(game_map)
        self.update_epilog(game_map, delta_time)

    def draw(self, screen, debug=False):
        if self.is_dead and \
           not self.is_best:
            return

        img = self._img_best if self.is_best else self._img_std

        if debug and self.is_best:
            img = img.copy()
            if self._cur_actions.get('brake', False):
                pygame.draw.circle(img, pygame.Color('red'), (3, img.get_height() // 2), 3)
            if self._cur_actions.get('decelerate', False):
                pygame.draw.circle(img, pygame.Color('white'), (3, img.get_height() // 2), 3)
            if self._cur_actions.get('left', False):
                pygame.draw.circle(img, pygame.Color('yellow'), (img.get_width() - 1, 1), 3)
            if self._cur_actions.get('right', False):
                pygame.draw.circle(img, pygame.Color('yellow'), (img.get_width() - 1, img.get_height() - 1), 3)

        img = pygame.transform.rotate(img, -self._body.heading).convert_alpha()
        rect = img.get_rect(center=self._body.pos)
        screen.blit(img, rect)

        self._sensors.draw(screen, debug)
