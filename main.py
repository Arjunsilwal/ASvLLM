import pygame
import asyncio
import argparse

from game_manager import GameManager

# This is the original, synchronous main function for your RAG simulation
def main_sync():
    game = GameManager(800, 800, mode='rag') # Tell the GM which mode to use
    game.run_sync() # Call the new synchronous run method

# --- NEW: A SINGLE ASYNC FUNCTION ---
# We pass the mode from the args into this function
# --- FIX: Changed 'mode_selection' to 'mode' to match the keyword argument ---
async def main_async(mode: str):
    game = GameManager(800, 800, mode=mode) # Use the mode
    await game.run_async() # Call the new asynchronous run method
# --- END FIX ---


if __name__ == "__main__":
    # Create a command-line argument parser
    parser = argparse.ArgumentParser(description="Run the ASV Simulation.")
    parser.add_argument(
        '--mode',
        type=str,
        # Ensure all your modes are listed
        choices=['rag', 'natural', 'hybrid', 'tss'],
        default='rag',
        help="Specify the simulation mode to run."
    )
    args = parser.parse_args()

    # --- UPDATED LOGIC ---
    # Launch the correct version based on the command-line argument
    if args.mode == 'natural':
        print("--- Running in NATURAL LANGUAGE mode (asynchronous) ---")
        asyncio.run(main_async(mode='natural')) # This call now works
    elif args.mode == 'hybrid':
        print("--- Running in HYBRID mode (asynchronous) ---")
        asyncio.run(main_async(mode='hybrid')) # This call now works
    elif args.mode == 'tss':
        print("--- Running in TSS mode (asynchronous) ---")
        asyncio.run(main_async(mode='tss')) # This call now works
    # Add your 'vision' mode back here if you still have it
    # elif args.mode == 'vision':
    #     print("--- Running in VISION mode (asynchronous) ---")
    #     asyncio.run(main_async(mode='vision'))
    else:
        print("--- Running in RAG mode (synchronous) ---")
        main_sync()