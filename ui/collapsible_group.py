import pygame

from config import BTN_BG, BTN_BORDER, TEXT_COLOR, GROUP_HEADER_H, GROUP_BUTTON_H, GROUP_PAD, GROUP_GAP


class CollapsibleGroup:
    """A simple collapsible group of buttons for the sidebar.

    Click the header to expand/collapse.
    """

    def __init__(self, title: str, buttons: list, expanded: bool = True):
        self.title = title
        self.buttons = buttons
        self.expanded = expanded

        self.header_rect = pygame.Rect(0, 0, 10, 10)
        self.hovered = False

        # Layout parameters (set in layout())
        self._header_h = GROUP_HEADER_H
        self._btn_h = GROUP_BUTTON_H
        self._gap = GROUP_GAP
        self._pad = GROUP_PAD
        self._w = 200

    def layout(self, x: int, y: int, w: int, header_h: int = GROUP_HEADER_H, btn_h: int = GROUP_BUTTON_H,
               pad: int = GROUP_PAD, gap: int = GROUP_GAP) -> int:
        """Position this group at (x,y) and return the next y after it."""
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
            y_cursor += pad - gap  # remove last gap, keep pad
        return y_cursor

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.header_rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.header_rect.collidepoint(event.pos):
                self.expanded = not self.expanded

        if self.expanded:
            for btn in self.buttons:
                btn.handle_event(event)

    def draw(self, surface, font):
        # Header
        header_color = (240, 240, 240) if self.hovered else BTN_BG
        pygame.draw.rect(surface, header_color, self.header_rect, border_radius=6)
        pygame.draw.rect(surface, BTN_BORDER, self.header_rect, 1, border_radius=6)

        arrow = "▾" if self.expanded else "▸"
        txt = font.render(f"{arrow} {self.title}", True, TEXT_COLOR)
        # Center-ish vertical alignment
        surface.blit(txt, (self.header_rect.x + 12, self.header_rect.y + (self._header_h - txt.get_height()) // 2))

        # Buttons
        if self.expanded:
            for btn in self.buttons:
                btn.draw(surface, font)
