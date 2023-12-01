import pygame as pg
import pygame.gfxdraw as gfxdraw

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.world.chunk import Chunk
    from src.world.tile import Tile



class Shadows:
    def __init__(self, chunk: "Chunk"):
        self.chunk = chunk
        self.tile_size = self.chunk.tile_size
        self.cube_height = self.chunk.cube_height
        self.main_surface = pg.Surface((self.chunk.width, self.chunk.height), pg.SRCALPHA)
        self.top_layer_surface = pg.Surface((self.chunk.width, self.chunk.height), pg.SRCALPHA)
        self.rect = self.chunk.rect
        self.shadow_color = (0, 0, 0, 150)
        self.shadow_size = 0.5 
        self.points = [
            (self.tile_size, 0), 
            (self.tile_size * 2, self.tile_size / 2), 
            (self.tile_size, self.tile_size), 
            (0, self.tile_size / 2)
        ]

    def draw(self, tile: "Tile", surface: pg.Surface):
        if tile.shadow_type == "none":
            return

        if tile.shadow_type == "full":
            full_face_points = [(x + tile.rect.x - self.rect.x, y + tile.rect.y - self.rect.y) for x, y in self.points]
            full_shadow_points = [(x + self.tile_size , y + self.cube_height * 2) for x, y in full_face_points]
            full_shadow_points[1] = (full_shadow_points[1][0] - self.tile_size * self.shadow_size, full_shadow_points[1][1] - self.cube_height * self.shadow_size)
            full_shadow_points[2] = (full_shadow_points[2][0] - self.tile_size * self.shadow_size, full_shadow_points[2][1] - self.cube_height * self.shadow_size)  
            gfxdraw.filled_polygon(surface, full_shadow_points, self.shadow_color)

        elif tile.shadow_type == "partial":
            partial_face_points = [(x + tile.rect.x + self.tile_size / 2  - self.rect.x, y + tile.rect.y - self.cube_height/2 - self.rect.y) for x, y in self.points]
            partial_shadow_points = [(x + self.tile_size , y + self.cube_height * 2) for x, y in partial_face_points]
            partial_shadow_points[0] = (partial_shadow_points[0][0] - self.tile_size / 2, partial_shadow_points[0][1] + (self.cube_height / 2))
            partial_shadow_points[1] = (partial_shadow_points[1][0] - self.tile_size, partial_shadow_points[1][1])
            partial_shadow_points[2] = (partial_shadow_points[2][0] - self.tile_size * self.shadow_size, partial_shadow_points[2][1] - self.cube_height * self.shadow_size)  
            gfxdraw.filled_polygon(surface, partial_shadow_points, self.shadow_color)

