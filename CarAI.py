
import pygame

from pygame.math import Vector2 as Vec

import numpy as np

import config

from Neuron import NeuralNetwork as NN

from Car import Car

class CarAI(Car):

    Car.__CONTROLS_SUBCLASSES__.append(NN)

    MAX_LIFE_COUNT_START = 50
    MAX_LIFE_COUNT_INC = 25
    LIFE_COUNT_CONSUMPTION_BASE = .5

    FITNESS_PARTS = [
        '_fitness_dist',
        '_fitness_stonemiles',
        '_fitness_laps',
    ]

    def __init__(self, start_pos, start_heading, map_gen, stonemiles_count_max, init_brain=True):
        super().__init__(start_pos, start_heading, map_gen, stonemiles_count_max)

        self._brain = None

        if init_brain:
            input_length = self._sensors.count + 1    # +1 for self._acceleration
            self._brain = NN(input_count=input_length,
                             hidden_count=20,
                             output_count=4,    # Left, Right, Accel, Brake
            )

    def reset(self):
        super().reset()

        self._max_life_count = self.MAX_LIFE_COUNT_START

        self._max_dist = 0
        self._kill_counter = 10

    def clone(self, map_gen, stonemiles_count_max):
        clone = self.__class__(self._body.start_pos, self._body.start_heading, map_gen, stonemiles_count_max, init_brain=False)
        clone._brain = self._brain.copy()
        return clone

    def dump(self, fname):
        self._brain.dump(fname)

    @staticmethod
    def load(start_pos, start_heading, map_gen, stonemiles_count_max, fname):
        car = CarAI(start_pos, start_heading, map_gen, stonemiles_count_max, init_brain=False)
        car._brain = NN.load(fname)
        return car

    def __repr__(self):
        details = ' + '.join([f'{getattr(self, part):.3}' for part in self.FITNESS_PARTS])
        return f'fitness {self.fitness:.3} ({details})'

    @property
    def _fitness_dist(self):
        coef = .01
        return self._max_dist * coef

    @property
    def _fitness_stonemiles(self):
        coef = 1.
        return self._stonemiles_count * coef

    @property
    def _fitness_laps(self):
        coef = 1000.
        return self._laps_count * coef

    @property
    def fitness(self):
        return sum(getattr(self, part) for part in self.FITNESS_PARTS)

    @property
    def life_count_consumption(self):
        return self.LIFE_COUNT_CONSUMPTION_BASE * (self._map_gen + 1)

    def mutate(self):
        self._brain.mutate(.1, .7)

    @classmethod
    def event(cls, event):
        super().event(event)

        NN.event(event)

    def _get_move_actions(self):
        inputs = np.array(self._sensors.get_all_sensors_length() + [self._body._acceleration])
        outputs = self._brain.forward(inputs)
        actions = {
            'left': outputs[0] > 0,
            'right': outputs[1] > 0,
            'accelerate': outputs[2] > 0,
            'brake': outputs[3] > 0,
        }

        #print(f'L/R:{outputs[0]:.3f} | U/D:{outputs[1]:.3f}')

        return actions

    def update_detection(self, game_map):
        super().update_detection(game_map)

        #//TEMP revoir si le kill_counter est toujours utile...
        if self._body._acceleration == 0.:
            self._kill_counter -= 1

        if self._kill_counter <= 0:
            #print(f'kill counter <= 0')
            self.dead()

        self._max_dist += self._body._acceleration

        self._max_life_count -= self.life_count_consumption

        if self._cur_stonemile > self._old_stonemile:
            self._max_life_count += self.MAX_LIFE_COUNT_INC

        if self._max_life_count < 0:
            print(f'max life count < 0 (consumption: {self.life_count_consumption})')
            self.dead()

    def _draw_brain(self, screen, debug=False):
        if not self.is_best:
            return

        self._brain.draw(screen, debug=debug)

    def draw(self, screen, debug=False):
        super().draw(screen, debug)
        self._draw_brain(screen, debug)
