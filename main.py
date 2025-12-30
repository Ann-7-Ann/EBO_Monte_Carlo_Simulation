import pygame
from config import *
from core.vector import Vector
from core.ray import Ray
from components.mirror import Mirror
from components.light_source import LightSource
from components.lens import Lens
from simulation.scene import Scene
from simulation.tracer import trace
from ui.grid import draw_grid
from ui.interaction import InteractionState

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


scene = Scene()
interaction = InteractionState()


scene.add(Mirror(Vector(400, 200), Vector(500, 300)))
scene.add(Lens(Vector(400, 500), Vector(600, 500),f=100))

source = LightSource(0, 250, 0)
ray = source.emit()

running = True
while running:
    mx, my = pygame.mouse.get_pos()
    mouse = Vector(mx, my)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for obj in reversed(scene.objects):
                if obj.contains_point(mouse):
                    interaction.dragging = obj
                    interaction.last_mouse = mouse
                    break
        if e.type == pygame.MOUSEMOTION:
            if interaction.dragging:
                dx = mouse.x - interaction.last_mouse.x
                dy = mouse.y - interaction.last_mouse.y
                interaction.dragging.move(dx, dy)
                interaction.last_mouse = mouse
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            interaction.dragging = None
            interaction.last_mouse = None

    screen.fill(BG)
    draw_grid(screen)

    trace(ray, scene, screen)

    for o in scene.objects:
        o.draw(screen)

    pygame.display.flip()
    clock.tick(1)

pygame.quit()
