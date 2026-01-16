import pygame

from config import BTN_BG, BTN_BG_HOVER, BTN_BORDER, TEXT_COLOR, GROUP_HEADER_H, GROUP_BUTTON_H, GROUP_PAD, GROUP_GAP, UI_TEXT_SECONDARY


class CollapsibleGroup:
    """Modern collapsible group with smooth animations and icons."""

    def __init__(self, title: str, buttons: list, expanded: bool = True):
        self.title = title
        self.buttons = buttons
        self.expanded = expanded
        self.expand_animation = 1.0 if expanded else 0.0

        self.header_rect = pygame.Rect(0, 0, 10, 10)
        self.hovered = False

        self._header_h = GROUP_HEADER_H
        self._btn_h = GROUP_BUTTON_H
        self._gap = GROUP_GAP
        self._pad = GROUP_PAD
        self._w = 200

    def layout(self, x: int, y: int, w: int, header_h: int = GROUP_HEADER_H, btn_h: int = GROUP_BUTTON_H,
               pad: int = GROUP_PAD, gap: int = GROUP_GAP) -> int:
        """Position this group and return next y."""
        self._header_h = header_h
        self._btn_h = btn_h
        self._gap = gap
        self._pad = pad
        self._w = w

        self.header_rect = pygame.Rect(x, y, w, header_h)
        y_cursor = y + header_h

        if self.expanded:
            y_cursor += pad
            for btn in self.buttons:
                btn.rect = pygame.Rect(x + pad, y_cursor, w - 2 * pad, btn_h)
                y_cursor += btn_h + gap
            y_cursor += pad - gap
        return y_cursor

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.header_rect.collidepoint(event.pos)
            # Change cursor to pointer when hovering header
            if self.hovered:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.header_rect.collidepoint(event.pos):
                self.expanded = not self.expanded

        if self.expanded:
            for btn in self.buttons:
                btn.handle_event(event)

    def draw(self, surface, font):
        # Header with modern styling
        header_color = BTN_BG_HOVER if self.hovered else BTN_BG
        pygame.draw.rect(surface, header_color, self.header_rect, border_radius=8)
        pygame.draw.rect(surface, BTN_BORDER, self.header_rect, 2, border_radius=8)

        # Category icon indicator (colored dot)
        icon_colors = {
            "Sources": (168, 85, 247),
            "Reflectors": (88, 199, 255),
            "Optics": (139, 92, 246),
            "Sensors": (239, 68, 68),
        }
        icon_color = icon_colors.get(self.title, (100, 200, 255))
        pygame.draw.circle(surface, icon_color, (self.header_rect.x + 16, self.header_rect.centery), 5)

        # Chevron tip only (< or >)
        arrow_x = self.header_rect.x + 32  # Moved to the right
        arrow_y = self.header_rect.centery
        arrow_size = 4
        line_width = 2  # Thicker
        
        if self.expanded:
            # Down chevron (v shape)
            pygame.draw.line(surface, TEXT_COLOR,
                           (arrow_x - arrow_size, arrow_y - 2),
                           (arrow_x, arrow_y + arrow_size), line_width)
            pygame.draw.line(surface, TEXT_COLOR,
                           (arrow_x + arrow_size, arrow_y - 2),
                           (arrow_x, arrow_y + arrow_size), line_width)
        else:
            # Right chevron (> shape)
            pygame.draw.line(surface, TEXT_COLOR,
                           (arrow_x - arrow_size, arrow_y - arrow_size),
                           (arrow_x, arrow_y), line_width)
            pygame.draw.line(surface, TEXT_COLOR,
                           (arrow_x - arrow_size, arrow_y + arrow_size),
                           (arrow_x, arrow_y), line_width)
        
        # Title text (no chevron character)
        txt = font.render(f"  {self.title}", True, TEXT_COLOR)
        surface.blit(txt, (self.header_rect.x + 35, self.header_rect.y + (self._header_h - txt.get_height()) // 2))

        # Buttons
        if self.expanded:
            for btn in self.buttons:
                btn.draw(surface, font)
