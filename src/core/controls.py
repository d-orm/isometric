import pygame as pg

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.app import App


class Controls:
    def __init__(self, app: "App"):
        self.app = app
        self.keys = pg.key.get_pressed()
        self.key_press_cd = 0.1
        self.key_press_timer = 0

    def update(self, dt):
        self.keys = pg.key.get_pressed()
        self.move_camera(dt)
        self.move_player(dt)

    def move_camera(self, dt):
        if self.keys[pg.K_w]:
            self.app.camera.move(0, 1, dt)
        if self.keys[pg.K_a]:
            self.app.camera.move(1, 0, dt)
        if self.keys[pg.K_s]:
            self.app.camera.move(0, -1, dt)
        if self.keys[pg.K_d]:
            self.app.camera.move(-1, 0, dt)

    def move_player(self, dt):
        if self.key_press_timer >= self.key_press_cd:
            if self.keys[pg.K_UP]:
                self.app.world.player.move(0, -1, dt)
            if self.keys[pg.K_LEFT]:
                self.app.world.player.move(-1, 0, dt)
            if self.keys[pg.K_DOWN]:
                self.app.world.player.move(0, 1, dt)
            if self.keys[pg.K_RIGHT]:
                self.app.world.player.move(1, 0, dt)
            self.key_press_timer = 0
        else:
            self.key_press_timer += dt

