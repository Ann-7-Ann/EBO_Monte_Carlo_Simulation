import pygame
from config import RAY_COLOR, MAX_BOUNCES, EPS

def trace(ray, scene, screen):
    pygame.draw.circle(
        screen,
        RAY_COLOR,
        ray.pos.tuple(),
        4
    )

    for _ in range(MAX_BOUNCES):
        obj, hit = scene.nearest_hit(ray)

        if not obj:
            end = ray.pos + ray.dir * 2000
            pygame.draw.line(
                screen,
                RAY_COLOR,
                ray.pos.tuple(),
                end.tuple(),
                1
            )
            break

        pygame.draw.line(
            screen,
            RAY_COLOR,
            ray.pos.tuple(),
            hit.tuple(),
            1
        )

        obj.interact(ray, hit)
        ray.pos = ray.pos + ray.dir * EPS
