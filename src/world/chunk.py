import pygame as pg

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.world.tile import Tile
    from src.core.camera import Camera
    from src.world.world import World

from src.world.shadows import Shadows


class Chunk:
    def __init__(self, world: "World", chunk_id: int, tiles: list["Tile"]):
        self.world = world
        self.chunk_id = chunk_id
        self.tiles = tiles
        self.tile_size = self.world.tile_size
        self.cube_height = self.world.cube_height
        self.chunk_size = self.world.chunk_size
        self.max_elevation = self.world.max_elevation
        self.width = self.chunk_size * self.tile_size * 2
        self.height = (self.chunk_size * self.tile_size) + (self.max_elevation * self.tile_size) + (self.tile_size * 4)
        self.main_surface = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.rect = self.main_surface.get_rect()
        self.shadows = Shadows(self)
        self.top_layer_tiles: list["Tile"] = []

    def update(self):
        self.rect.x = min(tile.rect.x for tile in self.tiles)
        self.rect.y = min(tile.rect.y for tile in self.tiles)

        for tile in self.tiles:
            if not tile.needs_layering:
                self.main_surface.blit(tile.image, (tile.rect.x - self.rect.x, tile.rect.y - self.rect.y))
                self.shadows.draw(tile, self.shadows.main_surface)
            else:
                self.shadows.draw(tile, self.shadows.main_surface)
                if tile.is_surface_tile:
                    self.top_layer_tiles.append(tile)

        self.main_surface.blit(self.shadows.main_surface, (0, 0))

    def draw_main_layer(self, screen: pg.Surface, camera: "Camera"):
        screen.blit(self.main_surface, camera.apply(self.rect))

    def add_tile(self, tile: "Tile"):
        self.tiles.append(tile)
