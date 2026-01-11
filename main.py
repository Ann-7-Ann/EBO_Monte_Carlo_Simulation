import pygame
from config import *
from core.vector import Vector
from core.ray import Ray
from components.mirror import Mirror
from sources.light_source import LightSource
from sources.fiber import FiberSource
from components.lens import Lens
from simulation.scene import Scene
from simulation.tracer import trace_rays
from ui.grid import draw_grid
from ui.interaction import InteractionState
from components.boundary import Boundary

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


scene = Scene()
interaction = InteractionState()

fiber = FiberSource(
    pos_x = 200,
    pos_y = 200,

)

rays = fiber.emit(num_rays=21)


# Add polygon boundaries as mirrors
polygon_points = [(100, 150), (50, 450), (950, 450), (950, 250), (750, 150)]
for i in range(len(polygon_points)):
    if i == 1:
        continue  # Skip one edge to create an opening
    p1 = Vector(*polygon_points[i])
    p2 = Vector(*polygon_points[(i + 1) % len(polygon_points)])
    scene.add(Boundary(p1, p2))

#scene.add(Lens(Vector(300, 150), Vector(314.05, 250),f=100))
scene.add(Lens(Vector(400, 150), Vector(385.95, 250),f=100))
scene.add(Mirror(Vector(600, 150), Vector(694.7, 250)))
scene.add(Lens(Vector(550, 450), Vector(750, 450),f=100))

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

    pygame.draw.line(screen, (0, 0, 255), (0, 200), (200, 200), 20)
    # Create a transparent surface
    polygon_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Draw filled polygon with transparency (last value in RGBA is alpha: 0=invisible, 255=opaque)
    pygame.draw.polygon(polygon_surface, (255, 255, 255, 50), [(100, 150), (50, 450), (950, 450), (950, 250), (750, 150)], 0)

    # Blit it onto the screen
    screen.blit(polygon_surface, (0, 0))

    trace_rays(rays, scene, screen)

    for o in scene.objects:
        o.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
