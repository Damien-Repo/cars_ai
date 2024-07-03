
import math
import pygame

from numba import jit, prange

import config

from Controls import Controls

from Map import Map

from CacheMath import CacheMath

class Sensors(Controls):

    __CONTROLS__ = {
        config.KEYS.CAR.DEBUG.SENSORS: 'Toggle drawing sensors',
    }

    SENSOR_SIZE_MAX = 300

    _draw_sensors = False

    _SENSORS_ANGLES = [-72, -36, 0, 36, 72]

    def __init__(self, body):
        self._body = body
        self._sensors_length = [0.] * self.count

    @property
    def count(self):
        return len(self._SENSORS_ANGLES)

    def get_all_sensors_length(self):
        return [s / self.SENSOR_SIZE_MAX for s in self._sensors_length]

    @classmethod
    def event(cls, event):
        if event.type == pygame.KEYDOWN:
            # Debug controls
            if cls.is_event_control(event, config.KEYS.CAR.DEBUG.SENSORS):
                cls._draw_sensors = not cls._draw_sensors

    @staticmethod
    @jit(nopython=True, fastmath=True, parallel=False)
    def _raycasting(sensors_angles, sensor_size_max, heading, pos_x, pos_y, array, w, h):
        sensors_length = [0.] * len(sensors_angles)
        for i in prange(len(sensors_angles)):
            angle = sensors_angles[i]
            rad = math.radians(angle + heading)
            sensors_length[i] = sensor_size_max
            for size in range(0, sensor_size_max, 1):
                x = pos_x + (math.cos(rad) * size)
                y = pos_y + (math.sin(rad) * size)
                if not (0 <= x <= w and \
                        0 <= y <= h and \
                        array[int(x), int(y), 0] == 255):
                    sensors_length[i] = size
                    break

        return sensors_length

    def _sensors_detection(self, game_map):
        self._sensors_length = self._raycasting(self._SENSORS_ANGLES, self.SENSOR_SIZE_MAX,
                                                self._body.heading,
                                                self._body.front_pos[0], self._body.front_pos[1],
                                                game_map.mask_array, game_map.mask_array.shape[0], game_map.mask_array.shape[1])

    def update_prolog(self, game_map):
        self._sensors_detection(game_map)

    def update_epilog(self, game_map):
        if self._draw_sensors:
            # Update sensors length after move to draw them correctly
            self._sensors_detection(game_map)

    def draw(self, screen, debug=False):
        if self._draw_sensors:
            start_pos = self._body.front_pos
            pygame.draw.circle(screen, (0, 255, 0), start_pos, 5)
            for angle, size in zip(self._SENSORS_ANGLES, self._sensors_length):
                rad = CacheMath.radians(angle + self._body.heading)
                end_pos = start_pos + (CacheMath.cos(rad) * size, CacheMath.sin(rad) * size)
                pygame.draw.line(screen, (255, 255, 255, 100), start_pos, end_pos)
