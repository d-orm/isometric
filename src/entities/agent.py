
import pygame as pg
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.camera import Camera

from src.world.tile import Tile



class Agent(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_grid_pos = self.grid_pos
        self.image = pg.Surface((self.tile_size * 2, self.tile_size + self.cube_height), pg.SRCALPHA)
        self.rect = self.image.get_rect()
        self.image_rect = self.image.get_rect()
        self.y_offset = self.tile_size // 6
        self.update_body_parts()

    def move(self, x, y, dt):
        self.current_grid_pos = self.current_grid_pos[0] + x, self.current_grid_pos[1] + y

    def head_bobbing(self):
        amp = 2
        freq = 0.02
        bobbing_offset = amp * math.sin(pg.time.get_ticks() * freq)
        self.head_pos.y += bobbing_offset        

    def update_grid_position(self):
        current_elevation = self.app.world.grid[self.current_grid_pos[1]][self.current_grid_pos[0]]
        current_elevation_offset = current_elevation * self.cube_height
        isometric_x = ((self.current_grid_pos[0] * self.tile_size) - (self.current_grid_pos[1] * self.tile_size))
        isometric_y = ((self.current_grid_pos[0] + self.current_grid_pos[1]) * self.tile_size // 2)  - current_elevation_offset - self.cube_height
        self.rect.x = isometric_x
        self.rect.y = isometric_y

    def update(self, dt):
        self.update_body_parts()
        self.update_grid_position()
        self.head_bobbing()

    def draw(self, screen: pg.Surface, camera: "Camera"):
        self.draw_body_parts()
        screen.blit(self.image, camera.apply(self.rect)) 

    def draw_body_parts(self) -> pg.Surface:
        self.image.fill((0, 0, 0, 0))
        pg.draw.rect(self.image, pg.Color("blue"), self.body_rect, border_radius=5)
        pg.draw.circle(self.image, pg.Color("pink"), self.left_hand_pos, self.hands_radius)
        pg.draw.circle(self.image, pg.Color("pink"), self.right_hand_pos, self.hands_radius)
        pg.draw.rect(self.image, pg.Color("brown"), self.left_foot_rect, border_radius=5)
        pg.draw.rect(self.image, pg.Color("brown"), self.right_foot_rect, border_radius=5)        
        pg.draw.circle(self.image, pg.Color("pink"), self.head_pos, self.head_radius)

    def update_body_parts(self) -> pg.Surface:
        # head circle
        self.head_radius = self.tile_size // 4
        self.head_pos = pg.Vector2(self.image_rect.centerx, self.image_rect.centery - self.head_radius - self.y_offset)
        # body
        self.body_width = self.tile_size // 2
        self.body_height = self.tile_size // 2
        self.body_pos = pg.Vector2(self.image_rect.centerx - self.body_width // 2, self.image_rect.centery - self.y_offset)
        self.body_rect = pg.Rect(*self.body_pos, self.body_width, self.body_height)
        # hands
        self.hands_width = self.tile_size // 6
        self.hands_radius = self.hands_width // 2
        self.left_hand_pos = pg.Vector2(self.body_rect.x - self.hands_radius, self.body_rect.centery)
        self.right_hand_pos = pg.Vector2(self.body_rect.x + self.body_width + self.hands_radius, self.body_rect.centery)
        # feet
        self.feet_width = self.tile_size // 3
        self.feet_height = self.tile_size // 5
        self.left_foot_pos = pg.Vector2(self.image_rect.centerx - self.feet_width, self.image_rect.centery + self.body_height - self.y_offset)
        self.left_foot_rect = pg.Rect(*self.left_foot_pos, self.feet_width, self.feet_height)
        self.right_foot_pos = pg.Vector2(self.image_rect.centerx, self.image_rect.centery + self.body_height - self.y_offset)
        self.right_foot_rect = pg.Rect(*self.right_foot_pos, self.feet_width, self.feet_height)

