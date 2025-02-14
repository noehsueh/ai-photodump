import os
import json

# Define the path to your album folder
album_folder = 'album'

# List all files that end with .jpg (you can add other image extensions if needed)
files = [f for f in os.listdir(album_folder) if f.lower().endswith('.jpg')]

# Save the list of files into album.json inside the album folder (or in the project root)
with open(os.path.join(album_folder, 'album.json'), 'w') as json_file:
    json.dump(files, json_file)

print("Album JSON file saved successfully! at ", os.path.join(album_folder, 'album.json'))