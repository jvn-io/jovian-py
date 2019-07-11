"""Utilities to install packages for a cloned gist"""
from __future__ import print_function
import subprocess
from time import sleep
from sys import stderr
from jovian.utils.anaconda import get_conda_bin, CONDA_NOT_FOUND
from jovian.utils.constants import ISSUES_MSG
from jovian.utils.logger import log
from jovian.utils.envfile import (check_error, check_pip_failed, extract_env_name,
                                  extract_env_packages, extract_pip_packages,
                                  identify_env_file, request_env_name, sanitize_envfile)


def run_command(command, env_fname, packages):
    # Run the command
    log('Executing:\n' + command + "\n")

    install_task = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
    # Extract the error (if any)
    _, error_string = install_task.communicate()
    error_string = error_string.decode('utf8', errors='ignore')
    if error_string:
        print(error_string, file=stderr)
        # Check for errors
        error, pkgs = check_error(error_string, packages=packages)
        pip_failed = check_pip_failed(error_string)

        if error:
            log('Installation failed!', error=True)
            log('Ignoring ' + error + ' dependencies and trying again...\n')
            sleep(1)
            sanitize_envfile(env_fname=env_fname, pkgs=pkgs)
            run_command(command=command, env_fname=env_fname, packages=packages)

        elif pip_failed:
            # TODO: Extract env details and run pip sub-command.
            # pip_packages = extract_pip_packages(env_fname=env_fname)
            return False
    else:
        # Print beta warning and github link
        log(ISSUES_MSG)
        return True


def install(env_fname=None, env_name=None):
    """Install packages for a cloned gist"""
    # Check for conda and get the binary path
    conda_bin = get_conda_bin()

    # Identify the right environment file, and exit if absent
    env_fname = identify_env_file(env_fname=env_fname)
    if env_fname is None:
        log('Failed to detect a conda environment YML file. Skipping..', error=True)
        return
    else:
        log('Detected conda environment file: ' + env_fname + "\n")

    # Get the environment name from user input
    env_name = request_env_name(env_name=env_name, env_fname=env_fname)
    if env_name is None:
        log('Environment name not provided/detected. Skipping..')
        return

    # Construct the command
    command = conda_bin + ' env update --file "' + \
        env_fname + '" --name "' + env_name + '"'

    packages = extract_env_packages(env_fname=env_fname)
    if len(packages) > 0:
        success = run_command(command=command, env_fname=env_fname, packages=packages)
        if success:
            print('Dependencies installed successfully.')
        else:
            print('Some pip packages failed to install.')


def activate(env_fname=None):
    """Read the conda environment file and activate the environment"""
    # Check for conda and get the binary path
    try:
        conda_bin = get_conda_bin()
    except:
        log(CONDA_NOT_FOUND, error=True)
        return False

    # Identify the right environment file, and exit if absent
    env_fname = identify_env_file(env_fname=env_fname)
    if env_fname is None:
        log('Failed to detect a conda environment YML file. Skipping..', error=True)
        return False
    else:
        log('Detected conda environment file: ' + env_fname + "\n")

    # Get the environment name from user input
    env_name = extract_env_name(env_fname=env_fname)
    if env_name is None:
        log('Environment name not provided/detected. Skipping..')
        return False

    # Activate the environment
    command = conda_bin + " activate " + env_name
    log('Executing:\n' + command + "\n")
    task = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)

    # Extract the error (if any)
    _, error_str = task.communicate()
    error_str = error_str.decode('utf8', errors='ignore')
    print(error_str)

    # TODO: Try again with `source` for older versions of conda
    # Need to check it across platforms

    # Print beta warning and github link
    log(ISSUES_MSG)
