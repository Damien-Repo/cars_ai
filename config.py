import pygame

class _Dict(dict):
    def __getattr__(self, key):
        ret = self.get(key)
        assert ret is not None, f"Unknown key ({key})"
        return ret

KEYS = _Dict(
    APP = _Dict(
        QUIT = pygame.K_ESCAPE,
    ),
    GAME = _Dict(
        NEXT = _Dict(
            RESET = pygame.K_r,
            GEN = pygame.K_n,
            MAP = pygame.K_m,
        ),
        DEBUG = _Dict(
            BEST_ONLY = pygame.K_b,
        ),
    ),
    MAP = _Dict(
        DEBUG = pygame.K_d,
        HIDE = pygame.K_h,
    ),
    CAR = _Dict(
        TURN_LEFT = pygame.K_LEFT,
        TURN_RIGHT = pygame.K_RIGHT,
        ACCELERATE = pygame.K_UP,
        DECELERATE = pygame.K_DOWN,
        BRAKE = pygame.K_SPACE,
        DEBUG = _Dict(
            SENSORS = pygame.K_s,
        ),
    ),
    NN = _Dict(
        DEBUG = _Dict(
            ACTIVATION = pygame.K_a,
        ),
    ),
)
