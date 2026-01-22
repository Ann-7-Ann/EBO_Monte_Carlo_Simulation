import pygame

from config import BTN_BG, BTN_BG_HOVER, BTN_BG_ACTIVE, BTN_BORDER, TEXT_COLOR, UI_TEXT_SECONDARY, GROUP_FIELD_H


class NumericField:
    """Clickable numeric field for the sidebar."""

    def __init__(self, label: str, get_value, set_value, unit: str = "", fmt: str = "{:.3f}"):
        self.label = label
        self.get_value = get_value
        self.set_value = set_value
        self.unit = unit
        self.fmt = fmt

        self.rect = pygame.Rect(0, 0, 10, GROUP_FIELD_H)
        self.hovered = False
        self.active = False
        self._text = ""

    def _current_text(self) -> str:
        try:
            v = self.get_value()
        except Exception:
            v = None
        if v is None:
            return ""
        try:
            return self.fmt.format(float(v))
        except Exception:
            return str(v)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self._text = self._current_text()
                return self  # request focus
            else:
                self.active = False

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return None
            if event.key == pygame.K_RETURN:
                try:
                    v = float(self._text)
                    self.set_value(v)
                except Exception:
                    pass
                self.active = False
                return None
            if event.key == pygame.K_BACKSPACE:
                self._text = self._text[:-1]
                return None

            ch = event.unicode
            allowed = "0123456789-+eE."
            if ch and ch in allowed:
                self._text += ch

        return None

    def draw(self, surface, font):
        bg = BTN_BG_ACTIVE if self.active else (BTN_BG_HOVER if self.hovered else BTN_BG)
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, BTN_BORDER, self.rect, 2, border_radius=8)

        label_surf = font.render(self.label, True, TEXT_COLOR)
        surface.blit(label_surf, (self.rect.x + 10, self.rect.y + (self.rect.height - label_surf.get_height()) // 2))

        val = self._text if self.active else self._current_text()
        if self.unit:
            val = f"{val} {self.unit}"

        val_surf = font.render(val, True, UI_TEXT_SECONDARY)
        surface.blit(val_surf, (self.rect.right - val_surf.get_width() - 10, self.rect.y + (self.rect.height - val_surf.get_height()) // 2))
