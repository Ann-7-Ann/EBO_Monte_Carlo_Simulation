import pygame
from config import GRID_COLOR

def draw_grid(screen):
    w, h = screen.get_size()
    for x in range(0, w, 50):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, h))
    for y in range(0, h, 50):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (w, y))
