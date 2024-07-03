
import pygame
from pygame.math import Vector2 as Vec

import config

from Controls import Controls

from Car import Car     # Use for Controls only

from CarManual import CarManual
from CarAI import CarAI

from Map import Map

class Game(Controls):

    LAPS_COUNT_MAX = 3

    __CONTROLS__ = {
        config.KEYS.GAME.NEXT.RESET: 'Reset game',
        config.KEYS.GAME.NEXT.GEN: 'Next generation',
        config.KEYS.GAME.NEXT.MAP: 'Next map',
    }
    __CONTROLS_SUBCLASSES__ = [ Car, Map ]

    def __init__(self, map_files, screen, pop_count=10, brain_file=None):
        self._pop_count = int(pop_count)
        self._cars = []

        self._border_color = (255, 255, 255)

        w, h = screen.get_size()
        self._view_map = screen.subsurface((0, 0), (w, h))  #//TEMP revoir plus tard le decoupage des subscreens
        self._view_brain = screen.subsurface((0, 0), (w, h))  #//TEMP revoir plus tard le decoupage des subscreens

        self._map = None
        self._map_screen = None
        self._map_files = map_files
        self._cur_map_index = -1
        self._map_gen = 0

        self._start_pos = None
        self._start_heading = None

        self._is_drawing_map = True
        self._is_drawing_best_only = False

        self._gen = 0
        self._best = None
        self._old_best = None

        self.load_next_map()
        self._populate(brain_file=brain_file)

    @property
    def is_manual_mode(self):
        return self._pop_count == 0

    def _get_start_pos(self):
        pt = self._map.path[0].start
        x, y = (pt.real, pt.imag)
        return (int(x), int(y))

    def _get_start_heading(self):
        pt_start = self._map.path[0].start
        pt_end = self._map.path[0].end

        vec_start = Vec(pt_start.real, pt_start.imag)
        vec_end = Vec(pt_end.real, pt_end.imag)
        angle = Vec().angle_to(vec_end - vec_start)

        return int(angle)

    def load_next_map(self):
        assert len(self._map_files) > 0, "Not any map file given"

        self._cur_map_index += 1
        if self._cur_map_index >= len(self._map_files):
            self._cur_map_index = 0
            self._map_gen += 1

        map_name = self._map_files[self._cur_map_index]

        self._map = Map(map_name)
        self._map_screen = pygame.Surface(self._map.size).convert_alpha()

        self._start_pos = Vec(self._get_start_pos())
        self._start_heading = self._get_start_heading()

        print(f'{self._map.stonemiles_count} stonemiles')

    def _populate(self, mutate=False, brain_file=None):
        self._cars = []

        if self.is_manual_mode:
            c = CarManual(self._start_pos, self._start_heading, self._map_gen, self._map.stonemiles_count)
            self._old_best = c
            self._best = c
            c.is_best = True
            self._cars.append(c)
            return

        # Populate from a pre-trained neuron network (aka brain)
        if brain_file is not None:
            loaded_car = CarAI.load(self._start_pos, self._start_heading, self._map_gen, self._map.stonemiles_count, brain_file)
            self._old_best = loaded_car
            self._best = loaded_car
            loaded_car.is_best = True
            self._cars.append(loaded_car)

        if mutate:
            # Populate with clones of the best car
            for _ in range(self._pop_count):
                c = self._best.clone(self._map_gen, self._map.stonemiles_count)
                if self._pop_count > 0:
                    c.mutate()
                self._cars.append(c)
        else:
            # Populate with full random new cars
            for _ in range(max(self._pop_count, 1)):
                c = CarAI(self._start_pos, self._start_heading, self._map_gen, self._map.stonemiles_count)
                self._cars.append(c)


    def reset_game(self):
        self._gen = 0
        self._best = None
        self._old_best = None

        self._populate()

    def event(self, event):
        if event.type == pygame.KEYDOWN:
            # Game controls
            if self.is_event_control(event, config.KEYS.GAME.NEXT.RESET):
                self.reset_game()
            if self.is_event_control(event, config.KEYS.GAME.NEXT.GEN):
                self.next_gen()
            if self.is_event_control(event, config.KEYS.GAME.NEXT.MAP):
                self.next_map()

        if self._best is not None:
            self._best.event(event)
        self._map.event(event)

    def _select_best(self):
        if self.is_manual_mode:
            return

        if self._best is not None:
            self._best.is_best = False

        self._best = max(self._cars, key=lambda x: x.fitness)

        self._best.is_best = True

    def next_gen(self):
        if self.is_manual_mode:
            return

        if self._old_best is not None:
            if self._old_best.fitness > self._best.fitness:
                print('  vvv keep old_best vvv')
                self._best = self._old_best

        print(f'#{self._map_gen}-{self._gen}: {self._best}')

        self._gen += 1
        self._old_best = self._best

        self._populate(mutate=True)

    def next_map(self):
        self.load_next_map()

        if not self.is_manual_mode:
            self._select_best()
            self._best.reset()
            self._old_best = self._best

        self._populate(mutate=True)

    def update(self, delta_time):
        alive_counter = 0
        for car in self._cars:
            if not car.is_dead:
                alive_counter += 1
                car.update(self._map, delta_time)

        self._select_best()

        if self._best.laps_count > self.LAPS_COUNT_MAX:
            self.next_map()

        if alive_counter == 0:
            self.next_gen()

    def _save_brain(self):
        if not self._old_best or \
            self.is_manual_mode:
            return

        fname = f'brains/car_MG{self._map_gen:03d}_G{self._gen:03d}_F{int(self._old_best.fitness):05d}.json'
        self._old_best.dump(fname)
        print(f' - Saved brain to: {fname}')

    def end_game(self):
        self._save_brain()

    def _draw_map(self, screen, debug=False):
        self._map_screen.fill((0, 0, 0, 0))      #//TEMP ici ou a la creation uniquement ?

        self._map.draw(self._map_screen)

        if not self._is_drawing_best_only:
            for car in self._cars:
                if not car.is_best:
                    car.draw(self._map_screen, debug)

        self._best.draw(self._map_screen, debug)

        w, h = self._view_map.get_size()
        centered_pos = self._best.pos - Vec(w // 2, h // 2)

        screen.blit(self._map_screen, (0, 0), (*centered_pos, *self._map_screen.get_size()))

    def draw(self, debug=False):
        self._draw_map(self._view_map, debug)
