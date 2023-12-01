import pygame as pg

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.app import App


class Camera:
    def __init__(self, app: "App"):
        self.app = app
        self.offset_x, self.offset_y = 0, 0
        self.speed = 1111 
        self.view_rect = pg.Rect(0, 0, app.screen_w, app.screen_h)

    def update(self):
        pass

    def move(self, x: int, y: int, dt: float):
        self.offset_x += x * self.speed * dt
        self.offset_y += y * self.speed * dt

    def apply(self, entity_rect: pg.Rect) -> pg.Rect:
        return entity_rect.move(self.offset_x, self.offset_y)
