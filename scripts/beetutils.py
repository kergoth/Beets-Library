#!/usr/bin/env/python3
# beetutils.py
# A collection of helper functions for managing a beets library
import os,fnmatch,sqlite3
from sys import version_info

def get_library_albums(library_dir):
    """
    Retrieve all paths to albums in a library

    Args:
        library_dir: Path to the library which contains the artist folders
    
    Returns:
        An array of full paths to albums in the library
    """

    library_albums = []

    # Create the paths to all artist subdirectories in the provided directory
    library_artists = [os.path.join(library_dir, file) for file in os.listdir(os.path.abspath(library_dir))]
	
    # Go through each artist in the library
    for library_artist in library_artists:
        # Append the full path to each album subdirectory within this artist subdirectory
        for library_album in os.listdir(library_artist):
            library_albums.append(os.path.join(library_artist, library_album))
    
    return library_albums

def get_folder_artifacts(folder, artifact_extension):
    """
    Retrieve all artifacts that match an extension within a folder

    Args:
        folder: Folder to list artifacts for
        artifact_extension: Extension to match artifacts for, or "dir" if listing directories
    
    Returns:
        An array of all artifact file paths that match an extension
    """

    artifacts = []

    if artifact_extension == "dir":
        for root, dirs, files in os.walk(folder):
            for directory in dirs:
                artifacts.append(os.path.join(root, directory))
    else:
        for root, dirs, files in os.walk(folder):
            for artifact in fnmatch.filter(files, "*.%s" % artifact_extension):
                artifacts.append(os.path.join(root, artifact))

    return artifacts

def get_beets_songs(db, extension="flac"):
    """
    Retrieve all paths to songs in a beets database

    Args:
        db: Path to the SQLite beets database
        extension: File extension of paths to return, if comparing converted files
    
    Returns:
        An array of all full song paths in a beets database
    """

    conn = sqlite3.connect(db)

    if version_info > (3, 0):
        beets_songs = [row[0].decode("UTF-8") for row in conn.execute("SELECT path FROM items")]
    else:
        beets_songs = [str(row[0]) for row in conn.execute("SELECT path FROM items")]
    
    return [os.path.splitext(beets_song)[0] + ".%s" % extension for beets_song in beets_songs]

def get_library_songs(library_dir, extension="flac"):
    """
    Retrieve all paths to songs in a music library

    Args:
        library_dir: Path to the library which contains the artist folders
        extension: Extension of song files, defaults to flac
    
    Returns:
        An array of all full song paths in a music library
    """

    pattern = "*.%s" % extension
    library_songs = []

    # Walk through each the entire directory structure of the library
    for root, dirs, files in os.walk(library_dir):
        # Append any .flac files found
        for filename in fnmatch.filter(files, pattern):
            library_songs.append(os.path.join(root, filename))
    
    return library_songs