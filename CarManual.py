
import pygame

import config

from Car import Car

class CarManual(Car):

    _MANUAL_MODE = True

    Car.__CONTROLS__.update({
        config.KEYS.CAR.TURN_LEFT: 'Turn car to left',
        config.KEYS.CAR.TURN_RIGHT: 'Turn car to right',
        config.KEYS.CAR.ACCELERATE: 'Accelerate car',
        config.KEYS.CAR.DECELERATE: 'Decelerate car',
        config.KEYS.CAR.BRAKE: 'Brake car',
    })

    def activate_manual_mode(self):
        self._MANUAL_MODE = True

    def dead(self):
        pass

    def _get_move_actions(self):
        keys = pygame.key.get_pressed()

        actions = {
            'left': keys[config.KEYS.CAR.TURN_LEFT],
            'right': keys[config.KEYS.CAR.TURN_RIGHT],
            'accelerate': keys[config.KEYS.CAR.ACCELERATE],
            'decelerate': keys[config.KEYS.CAR.DECELERATE],
            'brake': keys[config.KEYS.CAR.BRAKE],
        }

        return actions
