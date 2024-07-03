#!/usr/bin/env python3

import pygame
from pygame.locals import *
from pygame import Vector2 as Vec

from svgpathtools import svg2paths, Line, Path

def offset_curve(path, offset_distance, steps=100):
    """Takes in a Path object, `path`, and a distance,
    `offset_distance`, and outputs an piecewise-linear approximation
    of the 'parallel' offset curve."""
    nls = []
    for seg in path:
        ct = 1
        for k in range(steps):
            t = k / steps
            offset_vector = offset_distance * seg.normal(t)
            nl = Line(seg.point(t), seg.point(t) + offset_vector)
            nls.append(nl)
    connect_the_dots = [Line(nls[k].end, nls[k+1].end) for k in range(len(nls)-1)]
    if path.isclosed():
        connect_the_dots.append(Line(nls[-1].end, nls[0].end))
    offset_path = Path(*connect_the_dots)
    return offset_path

def build_path(screen):
    paths, _ = svg2paths('maps/spain.svg')
    path = paths[0]
    xmin, xmax, ymin, ymax = path.bbox()

    w, h = screen.get_size()
    padding = 10
    rw, rh = ((w - 0) / (xmax - xmin), (h - padding) / (ymax - ymin))
    path = path.translated(complex(-xmin + padding, -ymin + padding)).scaled(complex(min(rw, rh) * .9))

    return path

def draw_path(screen, path):
    n = 1000  # number of line segments to draw
    pts = [ (p.real,p.imag) for p in (path.point(i/n) for i in range(0, n+1))]
    for pt in pts:
        pygame.draw.circle(screen, pygame.Color('black'), (pt[0], pt[1]), 40)

    pygame.draw.aalines(screen, pygame.Color('white'), True, pts)


def main():
    pygame.init()
    screen = pygame.display.set_mode((1600, 900))

    path = build_path(screen)

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type in (QUIT, KEYDOWN):
                running = False

        ### Draw stuff
        screen.fill(pygame.Color('darkblue'))

        draw_path(screen, path)

        pygame.display.update()
        clock.tick(60)
        pygame.display.set_caption(f"FPS: {clock.get_fps():.2f}")


if __name__ == '__main__':
    main()