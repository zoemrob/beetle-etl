# Developer Documentation
Here we lay out important notes and guidelines to help developpers work their way around the BeetleETL code repository.

## Building Executables
Building Beetle as an executable relies on [pyinstaller](https://www.pyinstaller.org/) to take a working a script and then convert it to a standalone executable with python, and all package dependencies included. To build Beetle:

1. Ensure your python environment has the required packages installed (`i.e. conda or pip`)

2. Ensure you have a script using beetle which you can run via:

    ```
    > python my_beetle_script.py
    ```

    NOTE: the repo has a standard executable script setup for each operating system in the Builds folder.

2. Assuming you can run the script to build, then you can use pyinstaller to build an executable. The repo has a `builder.py` which takes the executable scripts and runs pyinstaller on them, but it is entirely possible for you to write and build your own scripts using Beetle.