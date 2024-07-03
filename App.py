#!/usr/bin/env python

import os
import sys
import pygame

import config

from Controls import Controls
from Game import Game

class App(Controls):

    W = 1500
    H = 975

    BG_COLOR = (10, 10, 50)

    __CONTROLS__ = {
        config.KEYS.APP.QUIT: 'Quit the program',
    }
    __CONTROLS_SUBCLASSES__ = [ Game ]

    def __init__(self, map_files, pop_count=0, brain_file=None):
        self._init_pygame(App.W, App.H)
        self._init_game(map_files, pop_count, brain_file)

        self.print_controls()

    def _init_pygame(self, width, height):
        self._w = width
        self._h = height

        pygame.init()
        info = pygame.display.Info()
        os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % ((info.current_w - self._w) / 2, 0)
        self._screen = pygame.display.set_mode((self._w, self._h))
        pygame.display.set_caption('Cars AI')

        self._clock = pygame.time.Clock()
        self._font = pygame.font.SysFont("freesansbold", 25)

        self._running = False

    def _init_game(self, maps_files, pop_count, brain_file):
        self._game = Game(maps_files, self._screen, pop_count, brain_file)

    @property
    def window_title(self):
        return f'Cars AI - FPS: {self._clock.get_fps():.2f}'

    @property
    def running(self):
        return self._running

    def events(self):
        for event in pygame.event.get():
            if event == pygame.NOEVENT:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == config.KEYS.APP.QUIT:
                    self._game.end_game()
                    self._running = False
                    return

            self._game.event(event)

    def update(self):
        delta_time = self._clock.get_time() / 1000

        self._game.update(delta_time)

    def draw(self):
        self._screen.fill(App.BG_COLOR)

        self._game.draw(debug=True)

        pygame.display.update()

    def run(self):
        self._running = True
        while self._running:
            self._clock.tick(60)
            pygame.display.set_caption(self.window_title)

            self.events()
            self.update()
            self.draw()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--pop_count', type=int, default=0)
    parser.add_argument('-m', '--map_files', nargs='+', default=None, required=True)
    parser.add_argument('-b', '--brain_file', default=None)
    args = parser.parse_args()

    a = App(map_files=args.map_files, pop_count=args.pop_count, brain_file=args.brain_file)
    a.run()
