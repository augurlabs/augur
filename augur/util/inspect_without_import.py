#needed as a workaround since python executes imported files
#This presents a problem since importing the phase functions themselves needs information from the config
#while the config needs the phase names before population
#The solution is to either make the user define the phase names seperate or to do this
#Which is to import the .py as text and parse the function names.

"""
This module lets us inspect Python files without actually importing them.

It uses Python's Abstract Syntax Tree (AST) to parse source files and extract specific 
function names. This is much safer and more robust than simple string parsing because 
it handles things like indentation, whitespace, comments, and decorators correctly.
"""

import ast
from pathlib import Path
from typing import List


def get_phase_names_without_import() -> List[str]:
    """
    Grabs the names of phase functions from start_tasks.py.
    
    Instead of importing the file (which runs code), we parse it strictly as text 
    using the AST module. We're looking for any function definition that has 
    '_phase' somewhere in its name.
    
    Returns:
        List[str]: A list of found function names, like 'prelim_phase' or 'secondary_repo_collect_phase'.
    
    Raises:
        FileNotFoundError: If we can't locate the start_tasks.py file.
        SyntaxError: If start_tasks.py has broken Python syntax.
    """
    current_file = Path(__file__).resolve()
    start_tasks_path = current_file.parent.parent / "tasks" / "start_tasks.py"
    
    try:
        source_code = start_tasks_path.read_text(encoding='utf-8')
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"We couldn't find start_tasks.py at {start_tasks_path}"
        ) from e
    
    try:
        tree = ast.parse(source_code, filename=str(start_tasks_path))
    except SyntaxError as e:
        raise SyntaxError(
            f"The file exists, but it contains invalid Python syntax: {e}"
        ) from e
    
    phase_names = []
    
    # We walk through every node in the abstract syntax tree
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # We want any function that identifies itself as a 'phase'
            if node.name.endswith('_phase'):
                phase_names.append(node.name)
    
    return phase_names