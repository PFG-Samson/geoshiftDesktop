# Utility functions

def ensure_dir(path):
    import os
    if not os.path.exists(path):
        os.makedirs(path)
