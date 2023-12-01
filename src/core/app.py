import pygame as pg
import asyncio
import sys

from src.world.world import World
from src.core.camera import Camera
from src.core.controls import Controls


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
        sys.exit()


