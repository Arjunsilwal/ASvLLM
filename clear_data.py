import os
import shutil

def clear_experiment_data():
    """
    Safely removes old logs and screenshots to ensure a fresh
    start for formal experimental runs.
    """
    folders_to_clear = ['logs', 'screenshots_natural', 'screenshots_vision']
    files_to_delete = ['llm_text_history_log.csv'] # Root level logs if any

    print("--- Starting Data Cleanup for New Experiment ---")

    # Clear Folders
    for folder in folders_to_clear:
        if os.path.exists(folder):
            print(f"Clearing folder: {folder}...")
            # We delete and recreate to ensure all subfiles are gone
            shutil.rmtree(folder)
            os.makedirs(folder)
        else:
            os.makedirs(folder)
            print(f"Created folder: {folder}")

    # Delete loose files
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
            print(f"Deleted file: {file}")

    print("--- Cleanup Complete. You are ready to start your experiment! ---")

if __name__ == "__main__":
    clear_experiment_data()