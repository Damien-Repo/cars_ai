#!/usr/bin/env python

import pygame
from pygame.math import Vector2 as Vec

class QuadTree():

    #@profile
    def __init__(self, boundary, capacity=5):
        self._boundary = pygame.Rect(boundary)
        self._capacity = capacity

        self._items = []

        self._subquadrants = []

        self._query_rect = None      # Used for debugging

        self.clear()

    #@profile
    def clear(self):
        self._items = []
        for s in self._subquadrants:
            s.clear()
        self._subquadrants = []

    #@profile
    def _subdivide(self):
        cx = self._boundary.centerx
        cy = self._boundary.centery
        left = self._boundary.left
        right = self._boundary.right
        top = self._boundary.top
        bottom = self._boundary.bottom

        ne = (cx, top, right - cx, cy - top)
        nw = (left, top, cx - left, cy - top)
        se = (cx, cy, right - cx, bottom - cy)
        sw = (left, cy, cx - left, bottom - cy)

        self._subquadrants = [
            QuadTree(ne, self._capacity),
            QuadTree(nw, self._capacity),
            QuadTree(se, self._capacity),
            QuadTree(sw, self._capacity),
        ]

    #@profile
    def insert(self, item : Vec, user_data=None):
        if not self._boundary.collidepoint(item):
            return False

        if len(self._items) < self._capacity:
            self._items.append((item, user_data))
            return True

        if len(self._subquadrants) == 0:
            self._subdivide()

        for sub in self._subquadrants:
            if sub.insert(item, user_data=user_data):
                return True

    #@profile
    def wrap_rect(self, rect):
        wrapped_rects = []

        resized_rect = rect.copy()
        W, H = self._boundary.size

        # Wrap corners
        if rect.left < 0 and rect.top < 0:
            resized_rect.topleft = (-1, -1)
            resized_rect.height += rect.top + 1
            resized_rect.width += rect.left + 1
            wrapped_rects.append(pygame.Rect(-1, H + rect.top, resized_rect.width, abs(rect.top) + 1))
            wrapped_rects.append(pygame.Rect(W + rect.left + 1, -1, abs(rect.left), resized_rect.height))
            wrapped_rects.append(pygame.Rect(W + rect.left + 1, H + rect.top, rect.width + rect.left, rect.height + rect.top))
        elif rect.right > W and rect.bottom > H:
            wrapped_rects.append(pygame.Rect(-1, rect.top, rect.right - W, rect.height - (rect.bottom - H) + 1))
            wrapped_rects.append(pygame.Rect(rect.left, -1, rect.width - (rect.right - W) + 1, rect.bottom - H))
            wrapped_rects.append(pygame.Rect(-1, -1, rect.right - W, rect.bottom - H))
            resized_rect.width -= rect.right - W - 1
            resized_rect.height -= rect.bottom - H - 1
        elif rect.left < 0 and rect.bottom > H:
            wrapped_rects.append(pygame.Rect(-1, -1, rect.width + rect.left + 1, rect.bottom - H))
            wrapped_rects.append(pygame.Rect(W + rect.left + 1, rect.top, abs(rect.left), rect.height - (rect.bottom - H) + 1))
            wrapped_rects.append(pygame.Rect(W + rect.left + 1, -1, abs(rect.left), rect.bottom - H))
            resized_rect.left = -1
            resized_rect.width += rect.left + 1
            resized_rect.height -= rect.bottom - H - 1
        elif rect.top < 0 and rect.right > W:
            wrapped_rects.append(pygame.Rect(rect.left, H + rect.top + 1, rect.width - (rect.right - W) + 1, abs(rect.top) + 1))
            wrapped_rects.append(pygame.Rect(-1, -1, rect.right - W, rect.height - (-1 - rect.top)))
            wrapped_rects.append(pygame.Rect(-1, H + rect.top + 1, rect.right - W, abs(rect.top)))
            resized_rect.top = -1
            resized_rect.height += rect.top + 1
            resized_rect.width -= rect.right - W - 1

        # Wrap edges
        elif rect.left < 0:
            wrapped_rects.append(pygame.Rect(W + rect.left + 1, rect.top, abs(rect.left) + 1, rect.height))
            resized_rect.left = -1
            resized_rect.width += rect.left + 1
        elif rect.top < 0:
            wrapped_rects.append(pygame.Rect(rect.left, H + rect.top + 1, rect.width, abs(rect.top) + 1))
            resized_rect.top = -1
            resized_rect.height += rect.top + 1
        elif rect.right > W:
            wrapped_rects.append(pygame.Rect(-1, rect.top, rect.right - W, rect.height))
            resized_rect.width -= (rect.right - 1) - W
        elif rect.bottom > H:
            wrapped_rects.append(pygame.Rect(rect.left, -1, rect.width, rect.bottom - H))
            resized_rect.height -= (rect.bottom - 1) - H

        return [resized_rect] + wrapped_rects

    #@profile
    def query(self, wanted_rect):
        found = []

        self._query_rect = wanted_rect
        if self._boundary.colliderect(wanted_rect) == -1:
            return []

        item_rect = pygame.Rect(0, 0, 3, 3)
        for item, user_data in self._items:
            item_rect.center = item
            if wanted_rect.colliderect(item_rect):
                #print(f'FOUND: {id(item)} center {item} in rect {wanted_rect}')
                found.append((item, user_data))

        for s in self._subquadrants:
            found.extend(s.query(wanted_rect))

        return found

    def draw(self, screen):
        pygame.draw.rect(screen, (127, 127, 127), self._boundary, 1)

        if self._query_rect is not None:
            pygame.draw.rect(screen, (255, 0, 0), self._query_rect, 1)

        for s in self._subquadrants:
            s.draw(screen)


if __name__ == '__main__':
    pass
