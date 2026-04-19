import re
import json
from pathlib import Path


def get_files(path):
    """
    Scans the directory for R dependency files.
    We look specifically for 'DESCRIPTION' files and 'renv.lock' files.
    """
    dir_path = Path(path)
    files = []
    
    # We look for both standard package metadata and renv lockfiles
    files.extend(list(dir_path.glob('**/DESCRIPTION')))
    files.extend(list(dir_path.glob('**/renv.lock')))
    
    return files


def get_deps_for_file(path):
    """
    Routes the file to the appropriate simple parser based on its name.
    """
    path_obj = Path(path)
    
    if path_obj.name == 'DESCRIPTION':
        return get_deps_from_description(path)
    elif path_obj.name == 'renv.lock':
        return get_deps_from_renv_lock(path)
    
    return []


def get_deps_from_description(path):
    """
    Extracts dependencies from a standard R DESCRIPTION file.
    
    We scan fields like Imports, Depends, Suggests, and others to find
    external package requirements.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        dependencies = set()
        
        # These are the standard sections where R packages list their requirements
        dependency_fields = ['Imports', 'Depends', 'Suggests', 'Enhances', 'LinkingTo']
        
        for field in dependency_fields:
            # We use regex to grab the whole section for a field.
            # It needs to handle potentially multi-line values.
            pattern = rf'^{field}:\s*(.*?)(?=^\S|\Z)'
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            
            if match:
                field_value = match.group(1)
                packages = parse_r_package_list(field_value)
                dependencies.update(packages)
        
        # 'R' itself is often listed as a dependency, but we only care about libraries
        dependencies.discard('R')
        
        return list(dependencies)
    
    except Exception:
        # If something goes wrong parsing, we just return nothing for this file
        return []


def parse_r_package_list(field_value):
    """
    Cleans up the raw text from the file to get a nice list of package names.
    """
    packages = set()
    
    # Flatten the text to a single line to make splitting easier
    field_value = ' '.join(field_value.split())
    
    parts = field_value.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # We need to grab the package name and ignore version numbers like (>= 1.0.0)
        # Note: We are currently stripping version info because the Augur dependency
        # model only tracks package names. If that changes, we can capture versions here.
        match = re.match(r'^([A-Za-z][A-Za-z0-9.]*)', part)
        if match:
            package_name = match.group(1).rstrip('.')
            if package_name:
                packages.add(package_name)
    
    return packages


def get_deps_from_renv_lock(path):
    """
    Parses an renv.lock file, which is just a JSON file listing specific package versions.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lockfile = json.load(f)
        
        dependencies = set()
        
        # renv.lock keeps everything under a 'Packages' key
        if 'Packages' in lockfile and isinstance(lockfile['Packages'], dict):
            for package_name in lockfile['Packages'].keys():
                dependencies.add(package_name)
        
        return list(dependencies)
    
    except (json.JSONDecodeError, Exception):
        return []
