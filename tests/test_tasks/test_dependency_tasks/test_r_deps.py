import json
import pytest
from augur.tasks.git.dependency_tasks.dependency_util import r_deps

def test_description_file_parsing(tmp_path):
    """
    Test that standard R DESCRIPTION files are parsed correctly,
    extracting dependencies from Depends, Imports, Suggests, and LinkingTo.
    """
    description_content = """Package: mypackage
Type: Package
Title: My Test Package
Version: 0.1.0
Author: Test Author
Maintainer: Test Author <test@example.com>
Description: A test package.
License: GPL-3
Encoding: UTF-8
LazyData: true
Depends:
    R (>= 3.5.0),
    dplyr (>= 1.0.0)
Imports:
    ggplot2,
    tidyr (>= 1.1.0),
    stringr
Suggests:
    testthat (>= 3.0.0),
    knitr,
    rmarkdown
LinkingTo:
    Rcpp (>= 1.0.0)
    """
    
    d_file = tmp_path / "DESCRIPTION"
    d_file.write_text(description_content, encoding="utf-8")
    
    deps = r_deps.get_deps_for_file(str(d_file))
    
    expected_deps = {'dplyr', 'ggplot2', 'tidyr', 'stringr', 'testthat', 
                     'knitr', 'rmarkdown', 'Rcpp'}
    
    # Assert we found exactly the expected dependencies
    assert set(deps) == expected_deps

def test_renv_lock_parsing(tmp_path):
    """
    Test that renv.lock JSON files are parsed correctly.
    """
    renv_lock_content = {
        "R": {"Version": "4.3.0", "Repositories": [{"Name": "CRAN", "URL": "https://cran.rstudio.com"}]},
        "Packages": {
            "ggplot2": {"Package": "ggplot2", "Version": "3.4.0", "Source": "Repository", "Repository": "CRAN"},
            "dplyr": {"Package": "dplyr", "Version": "1.1.0", "Source": "Repository", "Repository": "CRAN"},
            "tidyr": {"Package": "tidyr", "Version": "1.3.0", "Source": "Repository", "Repository": "CRAN"},
            "rmarkdown": {"Package": "rmarkdown", "Version": "2.20", "Source": "Repository", "Repository": "CRAN"}
        }
    }
    
    l_file = tmp_path / "renv.lock"
    measure = l_file.write_text(json.dumps(renv_lock_content), encoding="utf-8")
    
    deps = r_deps.get_deps_for_file(str(l_file))
    
    expected_deps = {'ggplot2', 'dplyr', 'tidyr', 'rmarkdown'}
    
    assert set(deps) == expected_deps

def test_file_discovery(tmp_path):
    """
    Test that the tool finds DESCRIPTION and renv.lock files recursively.
    """
    # Create a nested directory structure
    (tmp_path / 'DESCRIPTION').touch()
    (tmp_path / 'renv.lock').touch()
    
    subdir = tmp_path / 'subdir'
    subdir.mkdir()
    (subdir / 'DESCRIPTION').touch()
    
    nested = tmp_path / 'another' / 'nested'
    nested.mkdir(parents=True)
    (nested / 'renv.lock').touch()
    
    # Run the discovery
    files = r_deps.get_files(str(tmp_path))
    file_names = [f.name for f in files]
    
    assert file_names.count('DESCRIPTION') == 2
    assert file_names.count('renv.lock') == 2
