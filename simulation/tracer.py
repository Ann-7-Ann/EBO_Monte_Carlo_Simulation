import pygame
from config import RAY_COLOR, MAX_BOUNCES, EPS
from core.ray import Ray

def trace(ray, scene, screen):


    pos = ray.pos         
    direction = ray.dir

    for _ in range(MAX_BOUNCES):
        temp_ray = Ray(pos, direction)
        obj, hit = scene.nearest_hit(temp_ray)

        if not obj:
            end = pos + direction * 2000
            pygame.draw.line(
                screen,
                RAY_COLOR,
                pos.tuple(),
                end.tuple(),
                1
            )
            break

        pygame.draw.line(
            screen,
            RAY_COLOR,
            pos.tuple(),
            hit.tuple(),
            1
        )

        # interact updates direction only
        direction = obj.interact(direction,hit)
        
        if direction is None:
            break

        pos = hit + direction * EPS

def trace_rays(rays, scene, screen):
    for ray in rays:
        trace(ray, scene, screen)
