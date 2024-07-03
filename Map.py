#!/usr/bin/env python3

import pygame
from pygame.math import Vector2 as Vec

from svgpathtools import svg2paths, Line, Path

import config

from Controls import Controls

from QuadTree import QuadTree

class Map(Controls):

    __CONTROLS__ = {
        config.KEYS.MAP.DEBUG: 'Toggle drawing map debug',
        config.KEYS.MAP.HIDE: 'Toggle hide/show map',
    }
    #__CONTROLS_SUBCLASSES__ = [ ]

    SCREEN_PADDING = 10
    SEGMENTS_DRAW_LINE_COUNT = 1000

    POINTS_PER_SEGMENT = 100
    STONEMILES_COUNT_MAX = 100

    IRL_ROAD_WIDTH = 10
    PATH_RADIUS = 50
    assert PATH_RADIUS / IRL_ROAD_WIDTH == 5.        # Ratio Pixels/IRL enforced to 5

    COLOR_BG = pygame.Color('black')
    COLOR_PATH = pygame.Color('white')
    COLOR_PATH_BORDER_1 = pygame.Color('red')
    COLOR_PATH_BORDER_2 = pygame.Color('green')
    COLOR_STONEMILE = pygame.Color('orange')

    QUADTREE_BUCKET_SIZE = 5

    def __init__(self, filename):
        self._path = None

        self._image = None
        self._image_debug = None
        self._mask = None
        self._mask_array = None

        self._path_tree = None
        self._stonemiles = []
        self._build_path(filename)

        self._is_drawing = True
        self._is_drawing_debug = False

    @property
    def path(self):
        return self._path

    @property
    def size(self):
        assert self._image is not None
        return self._image.get_size()

    @property
    def stonemiles_count(self):
        return len(self._stonemiles)

    @property
    def mask_array(self):
        return self._mask_array

    def event(self, event):
        if event.type == pygame.KEYDOWN:
            # Map controls
            if self.is_event_control(event, config.KEYS.MAP.HIDE):
                self._is_drawing = not self._is_drawing

            # Debug controls
            if self.is_event_control(event, config.KEYS.MAP.DEBUG):
                self._is_drawing_debug = not self._is_drawing_debug

    def point_is_on_path(self, requested_point):
        w, h, _ = self._mask_array.shape
        if 0 <= requested_point.x <= w and \
            0 <= requested_point.y <= h:
            return self._mask_array[int(requested_point.x), int(requested_point.y), 0] == 255
        return False

    def get_path_point(self, requested_point):
        requested_point = Vec(requested_point)
        min_dist = self.PATH_RADIUS * 2
        ret = None

        rect = pygame.Rect((0, 0), (self.PATH_RADIUS * 2, self.PATH_RADIUS * 2))
        rect.center = requested_point

        path_points = self._path_tree.query(rect)
        #print(f'{len(path_points)} points in path')
        for pt, pt_i in path_points:
            d = requested_point.distance_to(pt)
            if d < min_dist and d < self.PATH_RADIUS:
                min_dist = d
                ret = (pt, pt_i)

        return ret

    def offset_curve(self, path, offset_distance, steps=10):
        """Takes in a Path object, `path`, and a distance,
        `offset_distance`, and outputs an piecewise-linear approximation
        of the 'parallel' offset curve."""
        nls = []
        for seg in path:
            for k in range(steps):
                t = k / steps
                if seg.end == seg.start:
                    continue
                offset_vector = offset_distance * seg.normal(t)
                nl = Line(seg.point(t), seg.point(t) + offset_vector)
                nls.append(nl)
        connect_the_dots = [Line(nls[k].end, nls[k+1].end) for k in range(len(nls)-1)]
        offset_path = Path(*connect_the_dots)
        return offset_path

    def _build_path_tree(self):
        stonemiles_cur = 0
        prev_stonemile_item = None

        for segment in self._path:
            for k in range(self.POINTS_PER_SEGMENT):
                t = k / self.POINTS_PER_SEGMENT
                item = Vec(segment.point(t).real, segment.point(t).imag)

                if prev_stonemile_item is None or \
                    prev_stonemile_item.distance_to(item) >= 100:
                    prev_stonemile_item = item
                    self._stonemiles.append(item)
                    self._path_tree.insert(item, user_data=stonemiles_cur)
                    stonemiles_cur += 1

    def _build_path(self, filename):
        paths, _ = svg2paths(filename)
        path = paths[0]
        xmin, xmax, ymin, ymax = path.bbox()

        self._path = path.scaled(complex(13.75))
        a,b,c,d = self._path.bbox()
        image_size = (b + 50, d + 50)

        self._path_tree = QuadTree((0, 0, image_size[0], image_size[1]), self.QUADTREE_BUCKET_SIZE)
        self._build_path_tree()

        pts = [(p.real,p.imag) for p in (self._path.point(i / self.SEGMENTS_DRAW_LINE_COUNT) for i in range(0, self.SEGMENTS_DRAW_LINE_COUNT))]

        self._image = pygame.Surface(image_size).convert_alpha()
        self._image.fill((0, 0, 0, 0))

        # Draw road
        for pt in pts:
            pygame.draw.circle(self._image, self.COLOR_BG, pt, self.PATH_RADIUS)

        # Draw road middle line
        for i in range(0, len(pts), 8):
            pygame.draw.line(self._image, self.COLOR_PATH, pts[i], pts[i+1], 1)

        # Create mask (collision)
        self._mask = pygame.mask.from_surface(self._image)
        self._mask_array = pygame.surfarray.array3d(self._mask.to_surface())

        # Create debug image
        self._image_debug = pygame.Surface(image_size).convert_alpha()
        self._image_debug.fill((0, 0, 0, 0))

        for radius, color in [(self.PATH_RADIUS, self.COLOR_PATH_BORDER_1),
                                (-self.PATH_RADIUS, self.COLOR_PATH_BORDER_2)]:
            border = self.offset_curve(self._path, radius)
            pts = [(p.real,p.imag) for p in (border.point(i / self.SEGMENTS_DRAW_LINE_COUNT) for i in range(0, self.SEGMENTS_DRAW_LINE_COUNT))]
            pygame.draw.aalines(self._image_debug, color, True, pts)

        for pt in self._stonemiles:
            pygame.draw.circle(self._image_debug, self.COLOR_STONEMILE, (pt.x, pt.y), 3)

    def draw(self, screen, debug=False):
        if not self._is_drawing:
            return

        screen.blit(self._image, (0, 0))

        if self._is_drawing_debug or debug:
            screen.blit(self._image_debug, (0, 0))
            #self._mask.to_surface(screen)
            #self._path_tree.draw(screen)


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((1500, 975))

    race_map = Map('maps/hungary.svg', screen.get_size())

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(pygame.Color('darkblue'))

        race_map.draw(screen, debug=True)

        x, y = pygame.mouse.get_pos()

        if race_map.point_is_on_path((x, y)):
            point = race_map.get_path_point((x, y))
            if point is not None:
                pt, _ = point
                pygame.draw.circle(screen, pygame.Color('yellow'), pt, Map.PATH_RADIUS)
            pygame.draw.circle(screen, pygame.Color('green'), (x,y), 5)
        else:
            pygame.draw.circle(screen, pygame.Color('red'), (x,y), 5)

        pygame.display.update()
        clock.tick(60)
        pygame.display.set_caption(f"FPS: {clock.get_fps():.2f}")
