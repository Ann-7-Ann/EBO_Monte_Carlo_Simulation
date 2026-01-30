import pygame
from config import BTN_BG, BTN_BG_HOVER, BTN_BORDER, TEXT_COLOR


class Button:
    """Modern button with hover effects and smooth transitions."""

    def __init__(self, x: int, y: int, w: int, h: int, text: str, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.hover_alpha = 0

    def draw(self, surface, font):
        # Smooth hover effect
        target_alpha = 255 if self.hovered else 0
        self.hover_alpha += (target_alpha - self.hover_alpha) * 0.15
        
        # Draw button background with rounded corners
        pygame.draw.rect(surface, BTN_BG_HOVER if self.hovered else BTN_BG, self.rect, border_radius=8)
        
        # Subtle border
        pygame.draw.rect(surface, BTN_BORDER, self.rect, 2, border_radius=8)
        
        # Text rendering - centered
        txt_surf = font.render(self.text, True, TEXT_COLOR)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            # Change cursor to pointer when hovering
            if self.hovered:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
