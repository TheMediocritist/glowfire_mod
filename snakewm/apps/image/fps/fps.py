# FPS counter for snakeware

import pygame
import pygame_gui

import time, statistics

MAXSAMP = 300

class SnakeFPS(pygame_gui.elements.UIWindow):
    def __init__(self, pos, manager):
        super().__init__(
            pygame.Rect(pos, (120, 131)),
            manager=manager,
            window_display_title="fps",
            object_id="#fps",
            resizable=False,
        )

        self.textbox = pygame_gui.elements.UITextBox(
            "",
            relative_rect=pygame.Rect(0, 0, 88, 80),
            manager=manager,
            container=self,
            anchors={
                "left": "left",
                "right": "right",
                "top": "top",
                "bottom": "bottom",
            },
        )
        self.last = 0
        self.samp = []

    def process_event(self, event):
        super().process_event(event)

    def update(self, time_delta):
        super().update(time_delta)

        fps = 1 / (time.time() - self.last)
        self.samp.append(fps)
        if len(self.samp) > MAXSAMP:
            self.samp = self.samp[-MAXSAMP:]
        self.last = time.time()

        self.set_text(
            "<font face='ProFont'><font pixel-size=14>FPS: %3u<p>AVG: %3u<p>MIN: %3u<p>MAX: %3u</font>"
            % (fps, statistics.mean(self.samp), min(self.samp), max(self.samp))
        )
        

    def set_text(self, text):
        self.textbox.html_text = text
        self.textbox.rebuild()
