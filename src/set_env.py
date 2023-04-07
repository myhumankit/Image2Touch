import contextlib
import os
import re
import sys

@contextlib.contextmanager
def set_env(**environ):
    """
    Temporarily set the process environment variables.
    https://stackoverflow.com/a/34333710

    >>> with set_env(PLUGINS_DIR=u'test/plugins'):
    ...   "PLUGINS_DIR" in os.environ
    True

    >>> "PLUGINS_DIR" in os.environ
    False

    :type environ: dict[str, unicode]
    :param environ: Environment variables to set
    """
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)

@contextlib.contextmanager
def set_blender_env():
    """
    Tries to find blender script files, and add them to the environment
    The files have to be in x.xx/scripts and x.xx/datafiles folders, where x.xx is the blender version
    Has to be done before importing bpy
    Useful for the exe version, making it truly portable
    """
    # Paths in which to look for Blender scripts
    possible_blender_locations = ['.']
    
    # We add the path to the script (python mode) or exe file (compiled mode) if it is different to the current path
    application_path = '.'
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    if(application_path != os.path.abspath('.')): 
        possible_blender_locations.append(application_path)
        
    # Looking fot blender scripts
    blender_dir_list = [f'{parent_dir}/{d}' 
                        for parent_dir in possible_blender_locations 
                        for d in os.listdir(parent_dir) 
                        if re.match(r'^[0-9]+\.[0-9]+$', d) and os.path.isdir(f'{parent_dir}/{d}/scripts')]
    
    if(len(blender_dir_list) > 0):
        # Blender files detected, will be added to the environment
        blender_dir = blender_dir_list[-1]
        print("Blender scripts found in folder '" + os.path.abspath(blender_dir) + "'")
        with set_env(BLENDER_SYSTEM_SCRIPTS = blender_dir + r"\scripts",
                     BLENDER_USER_DATAFILES = blender_dir + r"\datafiles"):
            yield
    else:
        # No blender files, environment is not changed
        print("Blender scripts not found in folder '" + os.path.abspath(".") + "', using default paths")
        yield