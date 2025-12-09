import pygame
import math


WIDTH, HEIGHT = 960, 540
BG_COLOR = (15, 23, 42)      # #0f172a
GRID_COLOR = (148, 163, 184) # #94a3b8 (z alpha)
RAY_COLOR = (255, 209, 102)  # #FFD166
MIRROR_COLOR = (0, 170, 255) # #00aaff
BEAM_COLOR = (56, 189, 248)  # #38bdf8
UI_BG = (243, 244, 246)      # #f3f4f6
BTN_BG = (255, 255, 255)
BTN_BORDER = (203, 213, 225)
TEXT_COLOR = (0, 0, 0)

MAX_BOUNCES = 10
MAX_RAY_LENGTH = 1000
EPS = 1e-4

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Beam Simulator)")
font = pygame.font.SysFont("Arial", 14)
title_font = pygame.font.SysFont("Arial", 18, bold=True)
clock = pygame.time.Clock()



class Vector:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other): return Vector(self.x + other.x, self.y + other.y)
    def __sub__(self, other): return Vector(self.x - other.x, self.y - other.y)
    def __mul__(self, scalar): return Vector(self.x * scalar, self.y * scalar)
    def dot(self, other): return self.x * other.x + self.y * other.y
    def length(self): return math.hypot(self.x, self.y)
    def normalize(self):
        l = self.length()
        if l == 0: return Vector(1, 0)
        return Vector(self.x / l, self.y / l)
    def to_tuple(self): return (self.x, self.y)

def distance_point_segment(px, py, x1, y1, x2, y2):
    
    A = px - x1
    B = py - y1
    C = x2 - x1
    D = y2 - y1
    dot = A * C + B * D
    len_sq = C * C + D * D
    param = -1
    if len_sq != 0:
        param = dot / len_sq
    
    if param < 0:
        xx, yy = x1, y1
    elif param > 1:
        xx, yy = x2, y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D
        
    dx = px - xx
    dy = py - yy
    return math.sqrt(dx * dx + dy * dy)

def intersect_ray_segment(ox, oy, dx, dy, x1, y1, x2, y2):
    
    rdx, rdy = dx, dy
    sdx, sdy = x2 - x1, y2 - y1
    rx, ry = x1 - ox, y1 - oy
    
    denom = rdx * sdy - rdy * sdx
    if abs(denom) < 1e-10: return None
    
    t = (rx * sdy - ry * sdx) / denom
    u = (rx * rdy - ry * rdx) / denom
    
    if t > EPS and 0 <= u <= 1:
        return t
    return None



class Mirror:
    def __init__(self, x1, y1, x2, y2):
        self.p1 = Vector(x1, y1)
        self.p2 = Vector(x2, y2)

    def draw(self, surface):
        pygame.draw.line(surface, MIRROR_COLOR, self.p1.to_tuple(), self.p2.to_tuple(), 4)
        pygame.draw.circle(surface, (255,255,255), (int(self.p1.x), int(self.p1.y)), 6)
        pygame.draw.circle(surface, (255,255,255), (int(self.p2.x), int(self.p2.y)), 6)

class Beam:
    def __init__(self, x1, y1, x2, y2):
        self.p1 = Vector(x1, y1)
        self.p2 = Vector(x2, y2)

    def draw(self, surface):
        pygame.draw.line(surface, BEAM_COLOR, self.p1.to_tuple(), self.p2.to_tuple(), 4)
        pygame.draw.circle(surface, (255,255,255), (int(self.p1.x), int(self.p1.y)), 6)
        pygame.draw.circle(surface, (255,255,255), (int(self.p2.x), int(self.p2.y)), 6)

class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hovered = False

    def draw(self, surface):
        color = (240, 240, 240) if self.hovered else BTN_BG
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, BTN_BORDER, self.rect, 1, border_radius=6)
        txt_surf = font.render(self.text, True, TEXT_COLOR)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.callback()



mirrors = [
    Mirror(400, 200, 600, 300),
    Mirror(500, 400, 800, 450)
]
beams = [
    Beam(140, HEIGHT/2 - 20, 140, HEIGHT/2 + 20)
]


dragging = None # "beamEnd", "beamRot", "mirror", "mirrorRot"
drag_target = None
add_mode = None # "mirror" or "beam"
start_pos = None
current_pos = None



def trace_ray(surface, sx, sy, dx, dy):
    ox, oy = sx, sy
    vx, vy = dx, dy
    remaining = MAX_RAY_LENGTH
    
    points_to_draw = [(ox, oy)]

    for _ in range(MAX_BOUNCES):
        best_t = remaining
        best_m = None
        
        
        for m in mirrors:
            t = intersect_ray_segment(ox, oy, vx, vy, m.p1.x, m.p1.y, m.p2.x, m.p2.y)
            if t and t < best_t:
                best_t = t
                best_m = m
        
        
        end_x = ox + vx * best_t
        end_y = oy + vy * best_t
        points_to_draw.append((end_x, end_y))
        
        remaining -= best_t
        
        if not best_m or remaining <= EPS:
            break
            
        
        ox, oy = end_x, end_y
        
        
        seg_dx = best_m.p2.x - best_m.p1.x
        seg_dy = best_m.p2.y - best_m.p1.y
       
        nx = -seg_dy
        ny = seg_dx
        n_len = math.hypot(nx, ny)
        if n_len > 0:
            nx /= n_len
            ny /= n_len
            
        # v' = v - 2*(v.n)*n
        dot = vx * nx + vy * ny
        vx = vx - 2 * dot * nx
        vy = vy - 2 * dot * ny
        
        
        ox += vx * EPS
        oy += vy * EPS

    
    if len(points_to_draw) > 1:
        pygame.draw.lines(surface, RAY_COLOR, False, points_to_draw, 1)

def draw_grid(surface):
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    s.set_alpha(20) # bardzo przezroczyste
    for x in range(0, WIDTH, 50):
        pygame.draw.line(s, (255,255,255), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(s, (255,255,255), (0, y), (WIDTH, y))
    surface.blit(s, (0,0))



def add_mirror_cb(): global add_mode; add_mode = "mirror"
def clear_mirrors_cb(): mirrors.clear()
def add_beam_cb(): global add_mode; add_mode = "beam"
def clear_beams_cb(): beams.clear()

buttons = [
    Button(20, 50, 90, 30, "Add Mirror", add_mirror_cb),
    Button(120, 50, 100, 30, "Clear Mirrors", clear_mirrors_cb),
    Button(230, 50, 90, 30, "Add Beam", add_beam_cb),
    Button(330, 50, 100, 30, "Clear Beams", clear_beams_cb),
]



running = True
while running:
    mx, my = pygame.mouse.get_pos()
    
    
    screen.fill(BG_COLOR)
    
   
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, 90))
    title = title_font.render("Beam Simulator with Multiple Mirrors", True, (0,0,0))
    screen.blit(title, (20, 15))
    hint = font.render("Beams: drag endpoints to resize, segment to rotate. Right-click to delete.", True, (100,117,137))
    screen.blit(hint, (450, 57))

    for btn in buttons:
        btn.draw(screen)

    
    canvas_area = pygame.Rect(0, 90, WIDTH, HEIGHT-90)
    
    screen.set_clip(canvas_area) 
    
    draw_grid(screen)

    
    for b in beams:
        
        b_vx = b.p2.x - b.p1.x
        b_vy = b.p2.y - b.p1.y
        b_len = math.hypot(b_vx, b_vy)
        
        
        emit_x, emit_y = b_vy, -b_vx
        emit_len = math.hypot(emit_x, emit_y)
        if emit_len > 0:
            emit_x /= emit_len
            emit_y /= emit_len
        else:
            emit_x, emit_y = 1, 0
            
        
        count = max(2, int(b_len / 2)) # Gęstość promieni
        for i in range(count):
            t = 0.5 if count == 1 else i / (count - 1)
            sx = b.p1.x + b_vx * t
            sy = b.p1.y + b_vy * t
            trace_ray(screen, sx, sy, emit_x, emit_y)

    
    for m in mirrors: m.draw(screen)
    for b in beams: b.draw(screen)

   
    if add_mode and start_pos and current_pos:
        preview_col = (134, 239, 172) if add_mode == "beam" else (125, 211, 252)
        pygame.draw.line(screen, preview_col, start_pos, current_pos, 2)

    screen.set_clip(None) 

    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        for btn in buttons:
            btn.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if not canvas_area.collidepoint(mx, my):
                continue
                
            if event.button == 3: 
                
                to_remove_b = None
                for b in beams:
                    if distance_point_segment(mx, my, b.p1.x, b.p1.y, b.p2.x, b.p2.y) < 8:
                        to_remove_b = b; break
                if to_remove_b: beams.remove(to_remove_b)
                
                
                to_remove_m = None
                for m in mirrors:
                    if distance_point_segment(mx, my, m.p1.x, m.p1.y, m.p2.x, m.p2.y) < 8:
                        to_remove_m = m; break
                if to_remove_m: mirrors.remove(to_remove_m)

            elif event.button == 1: 
                if add_mode:
                    start_pos = (mx, my)
                    current_pos = (mx, my)
                else:
                    
                    for b in beams:
                        if math.hypot(mx - b.p1.x, my - b.p1.y) < 10:
                            dragging, drag_target = "beamEnd", (b, "p1"); break
                        if math.hypot(mx - b.p2.x, my - b.p2.y) < 10:
                            dragging, drag_target = "beamEnd", (b, "p2"); break
                        if distance_point_segment(mx, my, b.p1.x, b.p1.y, b.p2.x, b.p2.y) < 8:
                            dragging, drag_target = "beamRot", b; break
                    
                    if not dragging:
                        for m in mirrors:
                            if math.hypot(mx - m.p1.x, my - m.p1.y) < 10:
                                dragging, drag_target = "mirror", (m, "p1"); break
                            if math.hypot(mx - m.p2.x, my - m.p2.y) < 10:
                                dragging, drag_target = "mirror", (m, "p2"); break
                            if distance_point_segment(mx, my, m.p1.x, m.p1.y, m.p2.x, m.p2.y) < 8:
                                dragging, drag_target = "mirrorRot", m; break

        elif event.type == pygame.MOUSEMOTION:
            if add_mode and start_pos:
                current_pos = (mx, my)
            elif dragging:
                if dragging == "beamEnd":
                    obj, pt = drag_target
                    if pt == "p1": obj.p1.x, obj.p1.y = mx, my
                    else:          obj.p2.x, obj.p2.y = mx, my
                elif dragging == "mirror":
                    obj, pt = drag_target
                    if pt == "p1": obj.p1.x, obj.p1.y = mx, my
                    else:          obj.p2.x, obj.p2.y = mx, my
                elif dragging in ["beamRot", "mirrorRot"]:
                    obj = drag_target
                    cx = (obj.p1.x + obj.p2.x) / 2
                    cy = (obj.p1.y + obj.p2.y) / 2
                    angle = math.atan2(my - cy, mx - cx)
                    length = math.hypot(obj.p2.x - obj.p1.x, obj.p2.y - obj.p1.y) / 2
                    obj.p1.x = cx - math.cos(angle) * length
                    obj.p1.y = cy - math.sin(angle) * length
                    obj.p2.x = cx + math.cos(angle) * length
                    obj.p2.y = cy + math.sin(angle) * length

        elif event.type == pygame.MOUSEBUTTONUP:
            if add_mode and start_pos:
                x1, y1 = start_pos
                x2, y2 = mx, my
                if math.hypot(x2-x1, y2-y1) > 5:
                    if add_mode == "mirror":
                        mirrors.append(Mirror(x1, y1, x2, y2))
                    else:
                        beams.append(Beam(x1, y1, x2, y2))
                start_pos = None
                current_pos = None
                add_mode = None
            dragging = None
            drag_target = None

    pygame.display.flip()
    clock.tick(60)

pygame.quit()