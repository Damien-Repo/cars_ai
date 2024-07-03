
import pygame

class Controls(object):

    __CONTROLS__ = {}
    __CONTROLS_SUBCLASSES__ = []

    @classmethod
    def __control_repr__(cls):
        text = [f'  {pygame.key.name(ctrl).upper()} => {desc}' for ctrl, desc in cls.__CONTROLS__.items() if ctrl is not None]
        for sub_cls in cls.__CONTROLS_SUBCLASSES__:
            text.append(sub_cls.__control_repr__())
        return '\n'.join(text)

    @classmethod
    def print_controls(cls):
        print(f'''
=========================
Controls:

{cls.__control_repr__()}
=========================
            ''')

    @classmethod
    def is_event_control(cls, event, key):
        assert key in cls.__CONTROLS__, f"Unexpected control key ({key}: {pygame.key.name(key)})"
        return event.key == key
