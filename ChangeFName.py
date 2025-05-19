import os

# === CONFIGURATION ===
folder_path = r'G:/Fan_art/Blushyspicy'  # Change to your folder path
new_name_pattern = 'Blushyspicy_'           # e.g., 'image_' will rename files to image_001.jpg, image_002.jpg, etc.
start_number = 1                      # Starting number for renamed files
file_extensions = ['.jpg', '.png','.jpeg']    # Only rename files with these extensions (or set to [] for all files)
preview_only = False                 # Set to False to actually rename the files

# === SCRIPT ===
def batch_rename_files(folder, pattern, start_num, extensions, preview):
    files = os.listdir(folder)
    files.sort()
    count = start_num

    for filename in files:
        file_path = os.path.join(folder, filename)
        if not os.path.isfile(file_path):
            continue
        name, ext = os.path.splitext(filename)
        if extensions and ext.lower() not in extensions:
            continue

        new_name = f"{pattern}{str(count).zfill(3)}{ext}"
        new_path = os.path.join(folder, new_name)

        if preview:
            print(f"Will rename: {filename} --> {new_name}")
        else:
            os.rename(file_path, new_path)
            print(f"Renamed: {filename} --> {new_name}")
        count += 1

# Run the script
batch_rename_files(folder_path, new_name_pattern, start_number, file_extensions, preview_only)
