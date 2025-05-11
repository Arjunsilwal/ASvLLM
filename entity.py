import pygame
import math
from response_parser import Maneuver

# Colors and font init...
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
pygame.font.init()
font = pygame.font.Font(None, 24)


def kmph_to_pixels_per_sec(kmph, pixels_per_km):
    if pixels_per_km <= 0:
        raise ValueError("pixels_per_km must be positive")
    return (kmph / 3600) * pixels_per_km


class ContextMenu:
    def __init__(self, x, y, options):
        self.x = x
        self.y = y
        self.options = options
        self.selected_option = None
        padding = 20
        max_text_width = 0
        for option in options:
            w, _ = font.size(option)
            max_text_width = max(max_text_width, w)
        self.width = max_text_width + padding
        self.row_height = 30
        self.height = len(options) * self.row_height

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        for i, option in enumerate(self.options):
            text = font.render(option, True, BLACK)
            screen.blit(text, (self.x + 10, self.y + 5 + i * self.row_height))

    def contains_point(self, pos):
        x, y = pos
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def handle_click(self, pos):
        if not self.contains_point(pos):
            return None
        idx = (pos[1] - self.y) // self.row_height
        if 0 <= idx < len(self.options):
            return self.options[idx]
        return None


class Vessel:
    def __init__(self, x, y, pixels_per_km, size=25, color=RED):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.color = color
        self.speed = 0.0
        self.acceleration = 2.028
        self.pixels_per_km = pixels_per_km
        self.max_speed_kmph = 67
        self.max_speed = kmph_to_pixels_per_sec(self.max_speed_kmph, pixels_per_km)
        self.slow_down_distance = 50.0
        self.goal = None
        self.selected = False
        self.heading = 0.0  # radians
        self.rect = pygame.Rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)
        self.desired_velocity = [0.0, 0.0]
        self.turn_rate = math.radians(10)
        self.in_maneuver = False

    @staticmethod
    def rotate_point(point, angle, origin):
        ox, oy = origin
        px, py = point
        qx = ox + math.cos(angle)*(px-ox) - math.sin(angle)*(py-oy)
        qy = oy + math.sin(angle)*(px-ox) + math.cos(angle)*(py-oy)
        return (qx, qy)

    def draw(self, screen):
        tip = (self.x, self.y - self.size/2)
        left = (self.x - self.size/3, self.y + self.size/2)
        right = (self.x + self.size/3, self.y + self.size/2)
        pts = [tip, left, right]
        rot = self.heading
        pts = [Vessel.rotate_point(p, rot, (self.x, self.y)) for p in pts]
        pygame.draw.polygon(screen, self.color, pts)
        if self.selected:
            pygame.draw.polygon(screen, GREEN, pts, 3)
        if self.goal:
            pygame.draw.circle(screen, BLUE, self.goal, 5)

    def set_selected(self, val):
        self.selected = val

    def contains_point(self, pos):
        return self.rect.collidepoint(pos)

    def turn_towards_goal(self, dt):
        if not self.goal or self.in_maneuver:
            return
        dx = self.goal[0] - self.x
        dy = self.goal[1] - self.y
        desired = (math.atan2(dy, dx) + math.pi/2) % (2*math.pi)
        diff = (desired - self.heading + math.pi) % (2*math.pi) - math.pi
        max_turn = self.turn_rate * dt
        if abs(diff) > max_turn:
            self.heading += max_turn if diff > 0 else -max_turn
        else:
            self.heading = desired
        self.heading %= (2*math.pi)

    def calculate_desired_velocity(self):
        vx = self.speed * math.sin(self.heading)
        vy = -self.speed * math.cos(self.heading)
        self.desired_velocity = [vx, vy]

    def update_position(self, dt):
        # adjust speed
        if self.goal or self.in_maneuver:
            dist = None
            if self.goal:
                dx, dy = self.goal[0]-self.x, self.goal[1]-self.y
                dist = math.hypot(dx, dy)
            if dist is None or dist > self.slow_down_distance:
                self.speed = min(self.speed + self.acceleration*dt, self.max_speed)
            else:
                self.speed = max(self.speed - self.acceleration*dt, 0)
            # move
            self.calculate_desired_velocity()
            self.x += self.desired_velocity[0]*dt
            self.y += self.desired_velocity[1]*dt
            self.rect.topleft = (self.x - self.size/2, self.y - self.size/2)
            # stop at goal
            if self.goal and dist is not None and dist < 5:
                self.goal = None
                self.speed = 0

    def apply_maneuver(self, maneuver, dt=1.0):
        # only adjust heading/speed
        self.in_maneuver = (maneuver != Maneuver.MAINTAIN_COURSE_SPEED)
        if maneuver == Maneuver.ALTER_COURSE_STARBOARD:
            self.heading += self.turn_rate*dt
        elif maneuver == Maneuver.ALTER_COURSE_PORT:
            self.heading -= self.turn_rate*dt
        elif maneuver == Maneuver.REDUCE_SPEED:
            self.speed = max(self.speed - self.acceleration*dt, 0)
        elif maneuver == Maneuver.PASS_ASTERN:
            self.heading += self.turn_rate*2*dt
            self.speed = max(self.speed - self.acceleration*dt, 0)
        # normalize
        self.heading %= (2*math.pi)


class USSTucker(Vessel):
    def __init__(self, x, y, pixels_per_km):
        super().__init__(x, y, pixels_per_km, size=30, color=(0,128,255))
        self.max_speed_kmph = 37
        self.max_speed = kmph_to_pixels_per_sec(self.max_speed_kmph, pixels_per_km)


class Francisco(Vessel):
    def __init__(self, x, y, pixels_per_km, size=30, color=BLUE):
        super().__init__(x, y, pixels_per_km, size=25, color=(0,128,255))
        self.max_speed_kmph = 187
        self.acceleration = 3.028
        self.max_speed = kmph_to_pixels_per_sec(self.max_speed_kmph, pixels_per_km)
        self.slow_down_distance = 50.0


class USSGerald(Vessel):
    pass
