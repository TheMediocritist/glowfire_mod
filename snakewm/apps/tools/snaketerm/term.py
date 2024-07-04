import sys
import traceback

from io import StringIO

import pygame
import pygame_gui
from pygame_gui.core import ObjectID
from pygame_gui.elements import UITextBox

import os
import json


class SnakeTerm(pygame_gui.elements.UIWindow):
    def __init__(self, pos, manager):
        super().__init__(
            pygame.Rect(pos, (380, 222)),
            manager,
            window_display_title="snaketerm",
            object_id="#snaketerm",
            resizable=True,
        )

        self.termbox = pygame_gui.elements.UITextBox(
            "",
            relative_rect=pygame.Rect(0, 0, 348, 143),
            manager=manager,
            container=self,
            anchors={
                "left": "left",
                "right": "right",
                "top": "top",
                "bottom": "bottom",
            },
            object_id=ObjectID(class_id="@snaketerm_textbox",
                               object_id="#snaketerm_termbox"
            ),
            allow_split_dashes=False
        )

        self.input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(0, -30, 348, 30),
            manager=manager,
            container=self,
            anchors={
                "left": "left",
                "right": "right",
                "top": "bottom",
                "bottom": "bottom",
            },
            object_id=ObjectID(class_id="@snaketerm_textentryline",
                               object_id="#snaketerm_inputbox"
            )
        )

        self.input.focus()

        # history attributes
        self.histsize = 100
        self.histindex = -1
        self.history = list()
        self.cached_command = str()

        # jump attributes
        self.jump_chars = (" ", "-", "_", "/")

        self.hotkeys = self.get_hotkeys()

        self.set_text('snaketerm ready.\n')

    def get_hotkeys(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:  # first attmept to load user hotkeys
            with open(current_dir + "/user_hotkeys.json", "r") as f:
                raw_json = json.load(f)
        except:  # if that file doesn't exist use default
            with open(current_dir + "/default_hotkeys.json", "r") as f:
                raw_json = json.load(f)
        # run through each value and add "self." then run through eval()
        key_config = {}
        for mod_key in raw_json.keys():
            key_config[mod_key] = {}
            for normal_key in raw_json[mod_key].keys():
                key_config[mod_key][normal_key] = eval(
                    "self." + raw_json[mod_key][normal_key]
                )
        return key_config

    def set_text(self, text):
        self.termbox.html_text = text.replace("\n", "<br>")
        self.termbox.rebuild()

    def clear_text(self):
        self.set_text(str())

    def jump_left(self):
        command = self.input.get_text()
        ep = self.input.edit_position
        while ep > 0 and command[ep - 1] not in self.jump_chars:
            ep -= 1
        self.input.edit_position = ep

    def jump_right(self):
        command = self.input.get_text()
        ep = self.input.edit_position
        while ep < len(command) and command[ep] not in self.jump_chars:
            ep += 1
        self.input.edit_position = ep

    def jump_backspace(self):
        command = self.input.get_text()
        ep = to_pos = self.input.edit_position
        while ep > 0 and command[ep - 1] not in self.jump_chars:
            ep -= 1
        self.input.set_text(command[:ep] + command[to_pos:])
        self.input.edit_position = ep

    def append_text(self, text, is_command=False):
        if is_command:
            self.termbox.html_text += ">>> " + text.replace("\n", "<br>") + "<br>"
            #self.termbox.html_text += "<font face=ProFont><font pixel_size=14> >>>"
        else:
            self.termbox.html_text += text.replace("\n", "<br>")
        self.termbox.rebuild()
        """
        if self.termbox.scroll_bar is not None:
            self.termbox.scroll_bar.scroll_position = (
                len(self.termbox.html_text.split("<br>")) * 5
            )
            self.termbox.scroll_bar.scroll_wheel_down = True
        """
        if self.termbox.scroll_bar:
            scroll_bar = self.termbox.scroll_bar
            scroll_bar.scroll_wheel_down = False
            scroll_bar.scroll_position += (250 * 1)
            scroll_bar.scroll_position = min(scroll_bar.scroll_position,
                                        scroll_bar.bottom_limit - scroll_bar.sliding_button.rect.height)
            x_pos = scroll_bar.rect.x + scroll_bar.shadow_width + scroll_bar.border_width
            y_pos = scroll_bar.scroll_position + scroll_bar.rect.y + scroll_bar.shadow_width + \
                    scroll_bar.border_width + scroll_bar.button_height
            scroll_bar.sliding_button.set_position(pygame.math.Vector2(x_pos, y_pos))

            scroll_bar.start_percentage = scroll_bar.scroll_position / scroll_bar.scrollable_height
            if not scroll_bar.has_moved_recently:
                scroll_bar.has_moved_recently = True

    def add_to_history(self, command):
        self.history = [command] + self.history
        if len(self.history) > self.histsize:
            del self.history[-1]

    def set_from_history(self):
        if self.histindex > -1:
            self.input.set_text(self.history[self.histindex])
        else:
            self.input.set_text(self.cached_command)
        self.input.edit_position = len(self.input.get_text())

    def set_histindex(self, increment):
        try:
            self.history[self.histindex + increment]
            self.histindex += increment
        except IndexError:
            pass
        return self.histindex

    def cache_command(self):
        self.cached_command = self.input.get_text()

    def flush_command_cache(self):
        self.cached_command = str()

    def process_event(self, event):
        super().process_event(event)

        if event.type == pygame.KEYUP and event.key == pygame.K_RETURN:
            _stdout = sys.stdout
            sys.stdout = tout = StringIO()

            input_command = self.input.get_text()
            try:
                code = compile(input_command, "snaketerm_code", "exec")
                exec(code, globals())
            except Exception:
                e_type, e_val, e_traceback = sys.exc_info()
                print("Traceback (most recent call last):")
                traceback.print_tb(e_traceback, None, tout)
                print(e_type, e_val)

            sys.stdout = _stdout
            result = tout.getvalue()
            self.append_text(input_command, is_command=True)
            self.append_text(result)
            self.add_to_history(input_command)
            self.histindex = -1
            self.flush_command_cache()
            self.input.set_text(str())

        # ctrl hotkeys
        elif pygame.key.get_mods() & pygame.KMOD_CTRL:
            if event.type == pygame.KEYUP:
                name = pygame.key.name(event.key)
                callback = self.hotkeys["ctrl"].get(name)
                if callback and callable(callback):
                    self.hotkeys["ctrl"][name]()

        # other special keys (history, etc)
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                increment = 1 if event.key == pygame.K_UP else -1
                if self.histindex == -1:
                    self.cache_command()
                self.set_histindex(increment)
                self.set_from_history()
