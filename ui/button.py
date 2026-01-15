import pygame
from config import BTN_BG, BTN_BORDER, TEXT_COLOR


class Button:
    """Small UI button used by the editor.

    Kept intentionally simple (hover + click). Inspired by PDP.py. 
    """

    def __init__(self, x: int, y: int, w: int, h: int, text: str, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hovered = False

    def draw(self, surface, font):
        color = (240, 240, 240) if self.hovered else BTN_BG
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, BTN_BORDER, self.rect, 1, border_radius=6)
        txt_surf = font.render(self.text, True, TEXT_COLOR)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        # click should work even without prior MOUSEMOTION
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
