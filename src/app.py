import pygame as pg
import pygame.gfxdraw as gfxdraw
from opensimplex import OpenSimplex
import asyncio
import math


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
        self.player = Player(self.app, None, 0, (0, 0), self.tile_size, self.cube_height, True, False, False, -1)
        self.river_surface, self.river_rect = self.create_river()

    def update(self):
        pass

    def draw(self, screen: pg.Surface, camera: "Camera"):
        for chunk in self.chunks:
            if camera.view_rect.colliderect(chunk.rect):
                chunk.draw_main_layer(screen, camera)

                entities = [(tile, tile.rect.y) for tile in chunk.top_layer_tiles]
                entities.append((self.player, self.player.rect.y))

                sorted_entities = sorted(entities, key=lambda x: x[1])

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


class Player(Tile):
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
        amp = 2  # amplitude of the bobbing, adjust as needed
        freq = 0.02  # frequency of the bobbing, adjust as needed
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


class App:
    def __init__(self):
        pg.init()
        self.screen_w, self.screen_h = 1920, 1040
        self.screen = pg.display.set_mode((self.screen_w, self.screen_h), pg.RESIZABLE | pg.SCALED)
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("Arial", 14)
        self.scale = 20
        self.tile_size = self.screen_h // self.scale
        self.world = World(
            self, 
            160, 160, 
            self.tile_size, 
            self.tile_size // 2, 
            7, 
            0.05
        )
        self.camera = Camera(self)
        self.controls = Controls(self)
        self.dt = 0

    async def run(self):
        while True:
            await asyncio.sleep(0.0)
            self.events: list[pg.event.Event] = pg.event.get()
            for event in self.events:
                if event.type == pg.QUIT \
                    or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                        self.quit()           
            self.screen.fill(pg.Color("black"))
            self.controls.update(self.dt)
            self.camera.update()
            self.world.draw(self.screen, self.camera)
            self.world.player.update(self.dt)
            self.world.update()
            pg.display.update()
            self.dt = self.clock.tick() / 1000.0
            pg.display.set_caption(f"FPS: {self.clock.get_fps():.2f}")
    
    
    def quit(self):
        pg.quit()
        exit()


if __name__ == "__main__":
    asyncio.run(App().run())
