import pygame as pg

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.app import App
    from src.core.camera import Camera


class Tile:
    def __init__(
            self, 
            app: "App", 
            image: pg.Surface, 
            elevation, 
            grid_pos, 
            tile_size, 
            cube_height, 
            shadow_type, 
            needs_layering, 
            is_surface_tile, 
            chunk_id
        ):
        self.app = app
        self.image = image
        self.elevation = elevation
        self.grid_pos = grid_pos
        self.tile_size = tile_size
        self.cube_height = cube_height
        self.shadow_type = shadow_type
        self.needs_layering = needs_layering
        self.is_surface_tile = is_surface_tile
        self.chunk_id = chunk_id

        isometric_x = (self.grid_pos[0] * self.tile_size) - (self.grid_pos[1] * self.tile_size)
        isometric_y = (self.grid_pos[0] + self.grid_pos[1]) * self.tile_size // 2
        elevation_offset = self.elevation * self.cube_height

        if self.image:
            self.rect = self.image.get_rect()
            self.rect.x = isometric_x
            self.rect.y = isometric_y - elevation_offset
   
    def draw(self, screen: pg.Surface, camera: "Camera"):
        screen.blit(self.image, camera.apply(self.rect))      
