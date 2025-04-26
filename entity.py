import pygame
import math
import enum

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
    if pixels_per_km <= 0: return 0
    return (kmph / 3600) * pixels_per_km


try:
    from response_parser import Maneuver
except ImportError:
    print("FATAL ERROR: Cannot import Maneuver enum from response_parser.py in entity.py!")


    # You might want to raise an error here or have a dummy class if absolutely necessary,
    # but fixing the import is the real solution.
    class Maneuver:  # Dummy class if import fails - NOT RECOMMENDED
        NO_ACTION = 0;
        ALTER_COURSE_STARBOARD = 1;
        ALTER_COURSE_PORT = 2
        MAINTAIN_COURSE_SPEED = 3;
        REDUCE_SPEED = 4;
        PASS_ASTERN = 5


class ContextMenu:
    def __init__(self, x, y, options):
        self.x = x
        self.y = y
        self.options = options
        self.selected_option = None
        padding = 20
        max_text_width = 0
        for option in options:
            text_width, _ = font.size(option)
            if text_width > max_text_width:
                max_text_width = text_width
        self.width = max_text_width + padding
        self.row_height = 30
        self.height = len(options) * self.row_height

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)
        for i, option in enumerate(self.options):
            text = font.render(option, True, BLACK)
            screen.blit(text, (self.x + 10, self.y + 5 + i * self.row_height))

    def handle_click(self, pos):
        if self.contains_point(pos):
            index = (pos[1] - self.y) // 30
            if 0 <= index < len(self.options):
                self.selected_option = self.options[index]
                return self.selected_option
        return None

    def contains_point(self, pos):
        x, y = pos
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


class Vessel:
    def __init__(self, x, y, pixels_per_km, size=30, color=RED):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.color = color
        self.speed = 0.0  # pixels per second
        self.acceleration = 2.028
        self.pixels_per_km = pixels_per_km
        self.max_speed_kmph = 97
        self.max_speed = kmph_to_pixels_per_sec(self.max_speed_kmph, self.pixels_per_km)  # pixels/sec
        self.slow_down_distance = 50.0  # pixels
        self.goal = None
        self.selected = False
        self.heading = 0.0  # radians, 0 = North, PI/2 = East
        self.rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
        self.desired_velocity = [0.0, 0.0]  # pixels/sec [vx, vy]
        self.turn_rate = math.radians(10)  # radians per second

    def rotate_point(point, angle, origin):
        ox, oy = origin
        px, py = point
        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return (qx, qy)

    def draw(self, screen):

        tip = (self.x, self.y - self.size / 2)
        left_base = (self.x - self.size / 3, self.y + self.size / 2)
        right_base = (self.x + self.size / 3, self.y + self.size / 2)
        points = [tip, left_base, right_base]

        rotation_angle = self.heading

        # Call the static method using the class name or self
        rotated_points = [Vessel.rotate_point(p, rotation_angle, (self.x, self.y)) for p in points]

        pygame.draw.polygon(screen, self.color, rotated_points)
        if self.selected:
            pygame.draw.polygon(screen, GREEN, rotated_points, 3)
        if self.goal:
            pygame.draw.circle(screen, BLUE, self.goal, 5)

    def set_selected(self, selected):
        self.selected = selected

    def contains_point(self, pos):
        return self.rect.collidepoint(pos)

    def turn_towards_goal(self, dt):
        if not self.goal or getattr(self, 'in_maneuver', False):
            return

        # Calculate the desired heading toward the goal.
        dx = self.goal[0] - self.x
        dy = self.goal[1] - self.y
        # Adjust by math.pi/2 if as vessel is drawn facing upward.
        desired_heading = math.atan2(dy, dx) + math.pi / 2
        desired_heading %= (2 * math.pi)
        # Compute the smallest angular difference.
        diff = (desired_heading - self.heading + math.pi) % (2 * math.pi) - math.pi

        # Calculate the maximum turn allowed for this frame.
        max_turn_this_frame = self.turn_rate * dt

        # If the difference is greater than the allowed turn, increment the heading by max_turn_this_frame.
        if abs(diff) > max_turn_this_frame:
            if diff > 0:
                self.heading += max_turn_this_frame
            else:
                self.heading -= max_turn_this_frame
        else:
            # When close enough, snap to the desired heading.
            self.heading = desired_heading

        self.heading %= (2 * math.pi)

    def calculate_desired_velocity(self):
        """Calculates velocity vector [vx, vy] based on current heading and speed."""
        vx = self.speed * math.sin(self.heading)
        vy = -self.speed * math.cos(self.heading)
        self.desired_velocity = [vx, vy]

    def update_position(self, dt):
        if self.goal:
            dx = self.goal[0] - self.x
            dy = self.goal[1] - self.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            # Adjust speed based on distance to goal
            if distance > self.slow_down_distance:
                self.speed = min(self.speed + self.acceleration * dt, self.max_speed)
            elif distance <= self.slow_down_distance:
                self.speed = max(self.speed - self.acceleration * dt, 0)

            # Apply desired_velocity (possibly adjusted by VO) scaled by current speed
            vel_magnitude = math.sqrt(self.desired_velocity[0] ** 2 + self.desired_velocity[1] ** 2)
            if vel_magnitude > 0:
                scale = min(self.speed, self.max_speed) / vel_magnitude  # Cap at max_speed
                self.x += self.desired_velocity[0] * scale * dt
                self.y += self.desired_velocity[1] * scale * dt

            self.rect.topleft = (self.x - self.size // 2, self.y - self.size // 2)

            # Stop if goal reached
            if distance < 1:
                self.goal = None
                self.speed = 0

    def apply_maneuver(self, maneuver_action, dt=1.0):
        """
        :param maneuver_action: a Maneuver enum
        """
        self.in_maneuver = True
        if maneuver_action == Maneuver.ALTER_COURSE_STARBOARD:
            self.heading += self.turn_rate * dt
        elif maneuver_action == Maneuver.ALTER_COURSE_PORT:
            self.heading -= self.turn_rate * dt
        elif maneuver_action == Maneuver.REDUCE_SPEED:
            self.speed = max(self.speed - self.acceleration * 0.5, 0)
        elif maneuver_action == Maneuver.PASS_ASTERN:
            self.heading += self.turn_rate * dt * 2
            self.speed = max(self.speed - self.acceleration, 0)
        elif maneuver_action == Maneuver.MAINTAIN_COURSE_SPEED:
            pass

        self.heading %= (2 * math.pi)


class USSTucker(Vessel):
    def __init__(self, x, y, pixels_per_km):
        super().__init__(x, y, pixels_per_km, size=80, color=(0, 128, 255))
        self.max_speed_kmph = 37
        self.max_speed = kmph_to_pixels_per_sec(self.max_speed_kmph, self.pixels_per_km)


class Francisco(Vessel):
    def __init__(self, x, y, pixels_per_km, size=30, color=BLUE):
        super().__init__(x, y, pixels_per_km, size=40, color=(0, 128, 255))
        self.max_speed_kmph = 107
        self.max_speed = kmph_to_pixels_per_sec(self.max_speed_kmph, self.pixels_per_km)
        self.slow_down_distance = 200.0


class USSGerald(Vessel):
    pass
