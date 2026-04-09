import pygame
import asyncio
from game_manager import GameManager
from env_utils import load_project_env


async def main():
    load_project_env()
    # Initialize pygame once at the start
    pygame.init()

    # 1000px provides enough room for the 5 dropdowns and 2 buttons in the nav bar
    screen_width = 1000
    screen_height = 1000

    game = GameManager(screen_width, screen_height)

    print("--- ASV LLM Simulator Started ---")
    print("Use the top navigation bar to select Scenario, LLM, and Mode.")

    try:
        await game.run_async()
    except Exception as e:
        print(f"Critical Error in async loop: {e}")
    finally:
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
