"""
Tests for the inspect_without_import module.

We want to make sure the AST-based function extraction works reliably
and doesn't get confused by weird formatting or extra comments.
"""

import ast
import os
import tempfile
import pytest
from augur.util.inspect_without_import import get_phase_names_without_import


class TestGetPhaseNamesWithoutImport:
    """Checking the main function logic."""
    
    def test_extracts_actual_phase_names(self):
        """Checks if we can actually pull the real phase names from start_tasks.py."""
        phase_names = get_phase_names_without_import()
        
        assert isinstance(phase_names, list)
        assert len(phase_names) > 0
        
        for name in phase_names:
            assert '_phase' in name, f"Function {name} doesn't seem to be a phase function."
        
        # These are the outputs of the original version of the function as of 7a46497aaed6c6dbecce9a1f8dda58282f9dd9fe
        expected_phases = [
            'prelim_phase',
            'primary_repo_collect_phase',
            'secondary_repo_collect_phase'
        ]
        
        for expected in expected_phases:
            assert expected in phase_names, f"We missed a required phase: '{expected}'"

        for actual in phase_names:
            assert actual in expected_phases, f"We have an extra phase: '{actual}'"

    
    def test_handles_different_indentation(self):
        """Ensures that messed up (but valid) indentation doesn't break anything."""
        test_code = '''
def test_phase(repo_git, full_collection):
    pass

class SomeClass:
    def another_phase(self, repo_git):
        pass

def    weirdly_spaced_phase   (repo_git):
    pass
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as file:
                tree = ast.parse(file.read())
            
            phase_names = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                    phase_names.append(node.name)
            
            assert 'test_phase' in phase_names
            assert 'another_phase' in phase_names
            assert 'weirdly_spaced_phase' in phase_names
            assert len(phase_names) == 3
        finally:
            os.unlink(temp_path)
    
    def test_handles_decorators(self):
        """Checks if functions with decorators are still picked up correctly."""
        test_code = '''
@some_decorator
def decorated_phase(repo_git):
    pass

@decorator_one
@decorator_two
def multi_decorated_phase(repo_git):
    pass

def normal_phase(repo_git):
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'decorated_phase' in phase_names
        assert 'multi_decorated_phase' in phase_names
        assert 'normal_phase' in phase_names
        assert len(phase_names) == 3
    
    def test_handles_type_hints(self):
        """Verifies that type hints in function signatures don't confuse the parser."""
        test_code = '''
from typing import Any

def typed_phase(repo_git: str, full_collection: bool) -> Any:
    pass

def partially_typed_phase(repo_git, full_collection: bool):
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'typed_phase' in phase_names
        assert 'partially_typed_phase' in phase_names
        assert len(phase_names) == 2
    
    def test_handles_multiline_definitions(self):
        """Makes sure definitions spanning multiple lines work fine."""
        test_code = '''
def multiline_phase(
    repo_git,
    full_collection,
    extra_param
):
    pass

def another_multiline_phase(
    repo_git: str,
    full_collection: bool,
    *args,
    **kwargs
) -> None:
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'multiline_phase' in phase_names
        assert 'another_multiline_phase' in phase_names
        assert len(phase_names) == 2
    
    def test_ignores_non_phase_functions(self):
        """Ensures we ignore functions that don't match our naming pattern."""
        test_code = '''
def some_phase(repo_git):
    pass

def unrelated_function(repo_git):
    pass

def helper_function():
    pass

def build_primary_phase_request():
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'some_phase' in phase_names
        assert 'unrelated_function' not in phase_names
        assert 'helper_function' not in phase_names
        
        # build_primary_phase_request actually has '_phase' in it, so it should be found.
        assert 'build_primary_phase_request' in phase_names
        
        assert len(phase_names) == 2
    
    def test_handles_comments_and_docstrings(self):
        """Verifies that comments and docstrings are completely ignored by the AST logic."""
        test_code = '''
# This is a comment about the phase
def commented_phase(repo_git):
    """
    This is a docstring.
    It can be multi-line.
    """
    # Internal comment
    pass

def another_phase(repo_git):
    """Single line docstring."""
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'commented_phase' in phase_names
        assert 'another_phase' in phase_names
        assert len(phase_names) == 2
    
    def test_handles_async_functions(self):
        """Checks if async functions are also detected if they have the right name."""
        test_code = '''
async def async_phase(repo_git):
    pass

def sync_phase(repo_git):
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        # AsyncFunctionDef is a different node type than FunctionDef
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'async_phase' in phase_names
        assert 'sync_phase' in phase_names
        assert len(phase_names) == 2
    
    def test_returns_list_of_strings(self):
        """Sanity check: we should always get back a list of strings."""
        phase_names = get_phase_names_without_import()
        
        assert isinstance(phase_names, list)
        for name in phase_names:
            assert isinstance(name, str)
    
    
    def test_no_duplicates(self):
        """Ensures we don't accidentally return the same function twice."""
        phase_names = get_phase_names_without_import()
        
        assert len(phase_names) == len(set(phase_names)), \
            f"Found duplicates: {phase_names}"

    def test_ignores_variables_with_matching_name(self):
        """Ensures that variables with '_phase' in their name are NOT picked up."""
        test_code = '''
this_is_a_variable_phase = 1

def actual_function_phase(repo_git):
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'actual_function_phase' in phase_names
        assert 'this_is_a_variable_phase' not in phase_names
        assert len(phase_names) == 1


class TestEdgeCases:
    """Testing some edge cases we might encounter."""
    
    def test_handles_empty_file(self):
        """An empty file shouldn't crash anything."""
        test_code = ''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert phase_names == []
    
    def test_handles_file_with_only_imports(self):
        """A file with just imports should yield no functions."""
        test_code = '''
import os
import sys
from typing import List
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert phase_names == []
    
    def test_handles_nested_functions(self):
        """Nested functions should be found if they match the naming pattern."""
        test_code = '''
def outer_phase(repo_git):
    def inner_phase(x):
        pass
    return inner_phase
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'outer_phase' in phase_names
        assert 'inner_phase' in phase_names
        assert len(phase_names) == 2


class TestRobustnessComparison:
    """
    Demonstrating why AST is better than string parsing.
    
    These tests show scenarios where basic string searching tends to fail but AST succeeds.
    """
    
    def test_string_parsing_would_fail_with_comment(self):
        """
        Naive string parsing often mistakenly picks up commented code.
        AST correctly ignores it.
        """
        test_code = '''
# def old_phase(repo_git):  # This is commented out
def actual_phase(repo_git):
    """
    This function used to be called def legacy_phase(repo_git)
    """
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        # AST should only see 'actual_phase'
        assert phase_names == ['actual_phase']
    
    def test_string_parsing_would_fail_with_unusual_spacing(self):
        """
        String parsing often relies on strict spacing (e.g., 'def name'),
        which breaks with tabs or extra spaces. AST doesn't care.
        """
        test_code = '''
def     unusual_spacing_phase     (repo_git):
    pass

def\ttab_phase(repo_git):
    pass
'''
        
        tree = ast.parse(test_code)
        phase_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and '_phase' in node.name:
                phase_names.append(node.name)
        
        assert 'unusual_spacing_phase' in phase_names
        assert 'tab_phase' in phase_names
