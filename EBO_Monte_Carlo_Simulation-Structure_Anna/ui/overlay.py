from config import OVERLAY_LINE_STEP


def draw_overlay_lines(screen, font, lines, x: int = 12, y: int = 95, color=(255, 255, 255)):
    """Draw a simple multi-line text overlay."""
    for line in lines:
        txt = font.render(line, True, color)
        screen.blit(txt, (x, y))
        y += OVERLAY_LINE_STEP
