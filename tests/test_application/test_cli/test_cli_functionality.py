import os
import pytest
import subprocess

def test_augur():

    FNULL = open(os.devnull, "w")
    command = "augur --help"
    process = subprocess.run(command.split(" "), stdout=FNULL, stderr=subprocess.STDOUT)

    assert process.returncode == 0

def test_main_dependency_install():

    FNULL = open(os.devnull, "w")
    command = "pip install -e ."
    process = subprocess.run(command.split(" "), stdout=FNULL, stderr=subprocess.STDOUT)

    assert process.returncode == 0

def test_data_analysis_dependency_installs():

    FNULL = open(os.devnull, "w")
    command = "scripts/install/workers.sh $target 2>&1 | tee logs/workers-install.log"
    process = subprocess.run(command.split(" "), stdout=FNULL, stderr=subprocess.STDOUT)

    assert process.returncode == 0
