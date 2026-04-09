import pygame
from typing import Optional, List

# UI Configuration
pygame.font.init()
FONT_UI = pygame.font.Font(None, 20)

COLOR_BG = (40, 44, 52)
COLOR_TEXT = (220, 220, 220)
COLOR_BORDER = (60, 64, 72)
COLOR_BUTTON_ACTION = (70, 130, 70)


class Button:
    def __init__(self, x, y, w, h, text, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.value = "running" if text == "PAUSE" else ""

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)
        txt_surf = FONT_UI.render(self.text, True, COLOR_TEXT)
        screen.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def update_text(self, new_text):
        self.text = new_text


class Dropdown:
    def __init__(self, x, y, w, h, options):
        self.rect = pygame.Rect(x, y, w, h)
        self.options = options
        self.selected_index = 0
        self.is_open = False

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_BG, self.rect, border_radius=4)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, 1, border_radius=4)
        txt = FONT_UI.render(self.options[self.selected_index], True, COLOR_TEXT)
        screen.blit(txt, (self.rect.x + 10, self.rect.y + 10))

        if self.is_open:
            for i, opt in enumerate(self.options):
                opt_rect = self.rect.copy()
                opt_rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(screen, COLOR_BG, opt_rect)
                pygame.draw.rect(screen, COLOR_BORDER, opt_rect, 1)
                txt_surf = FONT_UI.render(opt, True, COLOR_TEXT)
                screen.blit(txt_surf, (opt_rect.x + 10, opt_rect.y + 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            if self.is_open:
                for i in range(len(self.options)):
                    opt_rect = self.rect.copy()
                    opt_rect.y += (i + 1) * self.rect.height
                    if opt_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.is_open = False
                        return True
                self.is_open = False
        return False

    def get_selected_value(self):
        return self.options[self.selected_index]


class UIManager:
    def __init__(self, width):
        self.nav_bar_rect = pygame.Rect(0, 0, width, 60)

        # New Order: Mode -> LLM -> Scenario -> Prompt
        self.dropdowns = {
            "mode": Dropdown(10, 10, 120, 40, ["standard", "prompt_history", "natural"]),
            "llm": Dropdown(140, 10, 100, 40, ["openai", "claude", "deepseek"]),
            "scenario": Dropdown(250, 10, 180, 40, [
                "Head-On Scenario",
                "Cross Over Scenario",
                "Over Taking Scenario",
                "Multi vessel Scenario",
                "Multi vessel Scenario 2",
                "Multi vessel Scenario 3",
                "Traffic Separation Scenario"
            ]),
            "prompt": Dropdown(440, 10, 100, 40, ["minimal", "moderate", "detailed", "natural", "tss"])
            # Added tss here
        }

        self.action_buttons = {
            "load": Button(width - 210, 10, 90, 40, "LOAD", COLOR_BUTTON_ACTION),
            "pause": Button(width - 110, 10, 90, 40, "PAUSE", (160, 70, 70))
        }

    def handle_event(self, event: pygame.event.Event) -> dict:
        actions = {}
        dropdown_captured = False
        dropdown_keys = list(self.dropdowns.keys())
        for key in reversed(dropdown_keys):
            if self.dropdowns[key].handle_event(event):
                dropdown_captured = True
                break

        if not dropdown_captured:
            if self.action_buttons['load'].handle_event(event):
                actions['load'] = True
            if self.action_buttons['pause'].handle_event(event):
                btn = self.action_buttons['pause']
                btn.update_text("RESUME" if btn.text == "PAUSE" else "PAUSE")
                actions['pause'] = True
        return actions

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_BG, self.nav_bar_rect)
        pygame.draw.line(screen, COLOR_BORDER, (0, 60), (screen.get_width(), 60), 1)
        self.action_buttons['load'].draw(screen)
        self.action_buttons['pause'].draw(screen)
        for dd in self.dropdowns.values():
            dd.draw(screen)

    def get_value(self, key: str) -> Optional[str]:
        if key in self.dropdowns:
            return self.dropdowns[key].get_selected_value()
        return None