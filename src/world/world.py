import pygame as pg
import pygame.gfxdraw as gfxdraw
from opensimplex import OpenSimplex

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.app import App
    from src.core.camera import Camera
    
from src.world.tile import Tile
from src.world.chunk import Chunk
from src.entities.agent import Agent




class World:
    def __init__(self, app: "App", width, height, tile_size, cube_height, max_elevation, noise_scale, seed=0):
        self.app = app
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.cube_height = cube_height
        self.max_elevation = max_elevation
        self.seed = seed
        self.noise_scale = noise_scale
        self.simplex = OpenSimplex(seed=self.seed)
        self.chunk_size = self.app.scale * 4
        self.grass_tex = pg.image.load("assets/grass.jpg").convert_alpha()
        self.dirt_tex = pg.image.load("assets/dirt.jpg").convert_alpha()
        self.mask_tex = pg.Surface((self.tile_size * 3, self.tile_size + self.cube_height * 2), pg.SRCALPHA)
        self.mask_tex.fill((255, 0, 255, 255))
        self.player_tex = pg.image.load("assets/rock2.png").convert_alpha()
        self.grid = self.create_grid()
        self.top_layer_positions: list[tuple[int, int]] = []
        self.tiles: list["Tile"] = self.create_tiles()
        self.chunks: list["Chunk"] = self.create_chunks()
        self.player = Agent(self.app, None, 0, (0, 0), self.tile_size, self.cube_height, True, False, False, -1)
        self.river_surface, self.river_rect = self.create_river()

    def update(self):
        pass

    def draw(self, screen: pg.Surface, camera: "Camera"):
        for chunk in self.chunks:
            if camera.view_rect.colliderect(chunk.rect):
                chunk.draw_main_layer(screen, camera)

                entities: list["Tile"] = [(tile, tile.rect.y) for tile in chunk.top_layer_tiles]
                entities.append((self.player, self.player.rect.y))

                sorted_entities: list["Tile"] = sorted(entities, key=lambda x: x[1])

                for entity, _ in sorted_entities:
                    entity.draw(screen, camera)
                    if entity.grid_pos == self.player.current_grid_pos:
                        self.player.draw(screen, camera)

                self.draw_rivers(screen, camera)

    def create_river(self):
        points = [(0, 0), (0, 1), (1, 1), (1, 0)]
        for point in points:
            x, y = point
            elevation_offset = self.grid[y][x] * self.cube_height
            isometric_x = ((x * self.tile_size) - (y * self.tile_size)) + self.tile_size // 2
            isometric_y = ((x + y) * self.tile_size // 2)  - elevation_offset
            river_surface = pg.Surface((self.tile_size, self.tile_size), pg.SRCALPHA)
            river_rect = river_surface.get_rect()
            river_rect.x = isometric_x
            river_rect.y = isometric_y
            circle_radius = self.tile_size // 2
            circle_center = (circle_radius, circle_radius)
            pg.draw.circle(river_surface, pg.Color("blue"), circle_center, circle_radius)
        return river_surface, river_rect


    def draw_rivers(self, screen: pg.Surface, camera: "Camera"):
        screen.blit(self.river_surface, camera.apply(self.river_rect))

    def create_chunks(self) -> list["Chunk"]:
        print("creating chunks")
        num_chunks = max(tile.chunk_id for tile in self.tiles)
        chunks: list["Chunk"] = [Chunk(self, i, []) for i in range(num_chunks + 1)]

        for tile in self.tiles:
            chunks[tile.chunk_id].add_tile(tile)
        for chunk in chunks:
            chunk.update()

        return chunks

    def create_tiles(self) -> list["Tile"]:
        print("creating tiles")
        tiles = []
        grass_image_full = self.create_cube(self.grass_tex)
        grass_image_no_left_face = self.create_cube(self.grass_tex, left_face_visible=False)
        grass_image_no_right_face = self.create_cube(self.grass_tex, right_face_visible=False)
        grass_image_top_only = self.create_cube(self.grass_tex, left_face_visible=False, right_face_visible=False)

        dirt_image_full = self.create_cube(self.dirt_tex) 
        dirt_image_no_left_face = self.create_cube(self.dirt_tex, left_face_visible=False)
        dirt_image_no_right_face = self.create_cube(self.dirt_tex, right_face_visible=False)
        dirt_image_top_only = self.create_cube(self.dirt_tex, left_face_visible=False, right_face_visible=False)
        
        for y, row in enumerate(self.grid):
            for x, elevation in enumerate(row):
                # img = dirt_image if elevation % 2 == 0 else grass_image
                chunk_id = (x // self.chunk_size) + (y // self.chunk_size) * (self.height // self.chunk_size)

                needs_layering = not (not self.has_lower_northeast_neighbor(x, y) and not self.has_lower_northwest_neighbor(x, y) and not self.has_lower_north_neighbor(x, y))

                left_face_visible = not self.has_equal_or_higher_southwest_neighbor(x, y)
                right_face_visible = not self.has_equal_or_higher_southeast_neighbor(x, y)

                if elevation % 2 == 0:
                    tile_type = "dirt"
                else:
                    tile_type = "grass"

                if needs_layering:
                    if not left_face_visible and right_face_visible:
                        img = grass_image_no_left_face if tile_type == "grass" else dirt_image_no_left_face
                    elif left_face_visible and not right_face_visible:
                        img = grass_image_no_right_face if tile_type == "grass" else dirt_image_no_right_face
                    elif not left_face_visible and not right_face_visible:
                        img = grass_image_top_only if tile_type == "grass" else dirt_image_top_only
                    else:
                        img = grass_image_full if tile_type == "grass" else dirt_image_full
                else:
                    img = grass_image_full if tile_type == "grass" else dirt_image_full


                for elev in range(elevation + 1):
                    has_shadow = False if elev != elevation and elevation != 0 else self.has_lower_southeast_neighbor(x, y)
                    is_surface_tile = elev == elevation       
                    shadow_type = "partial" if has_shadow and self.has_equal_or_higher_south_neighbor(x, y) else "full" if has_shadow else "none"
                    tiles.append(Tile(
                                self.app, 
                                img, 
                                elev, 
                                (x, y), 
                                self.tile_size, 
                                self.cube_height, 
                                shadow_type, 
                                needs_layering, 
                                is_surface_tile, 
                                chunk_id
                            ))

        return tiles

    def has_neighbor_with_condition(self, x, y, dx, dy, condition):
        neighbor_x, neighbor_y = x + dx, y + dy
        if 0 <= neighbor_x < self.width and 0 <= neighbor_y < self.height:
            neighbor_elevation = self.grid[neighbor_y][neighbor_x]
            return condition(self.grid[y][x], neighbor_elevation)
        return False

    def is_edge_tile(self, x, y):
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return any(self.has_neighbor_with_condition(x, y, dx, dy, lambda e, ne: ne < e) for dx, dy in neighbors)

    def has_lower_northeast_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, 0, -1, lambda e, ne: ne < e)

    def has_lower_north_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, -1, -1, lambda e, ne: ne < e)

    def has_lower_northwest_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, -1, 0, lambda e, ne: ne < e)

    def has_lower_southeast_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, 1, 0, lambda e, ne: ne < e)

    def has_equal_or_higher_south_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, 1, 1, lambda e, ne: ne >= e)
    
    def has_equal_or_lower_southwest_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, 0, 1, lambda e, ne: ne <= e)
    
    def has_equal_or_lower_southeast_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, 1, 1, lambda e, ne: ne <= e)
    
    def has_equal_or_higher_southeast_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, 1, 0, lambda e, ne: ne >= e)
    
    def has_equal_or_higher_southwest_neighbor(self, x, y):
        return self.has_neighbor_with_condition(x, y, 0, 1, lambda e, ne: ne >= e)

    def is_neighbor_within_bounds(self, x, y, dx, dy):
        """ Check if the neighbor at the given offset is within the world bounds. """
        neighbor_x = x + dx
        neighbor_y = y + dy
        return 0 <= neighbor_x < self.width and 0 <= neighbor_y < self.height

    def southeast_neighbor_out_of_bounds(self, x, y):
        return not self.is_neighbor_within_bounds(x, y, 1, 0)
    
    def southwest_neighbor_out_of_bounds(self, x, y):
        return not self.is_neighbor_within_bounds(x, y, 0, 1)
    
    def create_grid(self) -> list[list[int]]:
        return [
            [int((self.simplex.noise2(x * self.noise_scale, y * self.noise_scale) + 1) / 2 * self.max_elevation)
            for x in range(self.width)] for y in range(self.height)
        ]

    def get_cube_points(self) -> tuple[list[tuple[int, int]]]:
        top_face_points = [
            (self.tile_size, 0), 
            (self.tile_size * 2, self.tile_size / 2), 
            (self.tile_size, self.tile_size), 
            (0, self.tile_size / 2)
        ]
        left_face_points = [
            (0, self.tile_size / 2), 
            (self.tile_size, self.tile_size), 
            (self.tile_size, self.tile_size + self.cube_height), 
            (0, self.tile_size / 2 + self.cube_height)
        ]
        right_face_points = [
            (self.tile_size, self.tile_size), 
            (self.tile_size * 2, self.tile_size / 2), 
            (self.tile_size * 2, self.tile_size / 2 + self.cube_height), 
            (self.tile_size, self.tile_size + self.cube_height)
        ]
        return top_face_points, left_face_points, right_face_points

    def create_cube(self, texture:pg.Surface, left_face_visible:bool=True, right_face_visible:bool=True, apply_shading:bool=True) -> pg.Surface:
        surface = pg.Surface((self.tile_size * 2, self.tile_size + self.cube_height), pg.SRCALPHA)

        top_face_points, left_face_points, right_face_points = self.get_cube_points()

        texture_top = pg.transform.scale(texture, (self.tile_size * 2, self.tile_size))
        texture_left = pg.transform.scale(texture, (self.tile_size, self.cube_height))
        texture_right = pg.transform.scale(texture, (self.tile_size, self.cube_height))

        if apply_shading:
            texture_left.fill((200, 200, 200, 255), None, pg.BLEND_RGBA_MULT)
            texture_right.fill((150, 150, 150, 255), None, pg.BLEND_RGBA_MULT)

        gfxdraw.textured_polygon(surface, top_face_points, texture_top, 0, 0)
        if left_face_visible:
            gfxdraw.textured_polygon(surface, left_face_points, texture_left, 0, 0)
        if right_face_visible:
            gfxdraw.textured_polygon(surface, right_face_points, texture_right, 0, 0)

        return surface
 