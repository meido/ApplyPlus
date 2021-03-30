# ApplyPlus

This program is used for detecting patches that do not apply cleanly to source and attempting to apply them, taking into account changes in the patch context and lines being added/removed by the patch.

As part of the background research, a collection of patches of the Linux Kernel was examined.  For patches that did not apply cleanly, the reason for the failure was documented in a [Kernel Patch Classification Spreadsheet](https://docs.google.com/spreadsheets/d/1hCqyOZA-nplliI-bdGzt6IMTdFmO5hQp88RwCge0wcw/edit?usp=sharing), with a [Kernel Patch Classification Write up](https://docs.google.com/document/d/134bmSlemKDy2chgjqK3wxQGC0PsluSVZDMMZgkTlp_Y/edit?usp=sharing)

## Building

1. Run `make build`.  This will create a python virtualenv environment so that the packages we need don't pollute the system wide python namespace.  Within the virtualenv, it'll download the needed packages.

## Running the patch script

In order to run the patch script, you need to:

1. Initialize the virtualenv created during the build

    `. ./env/bin/activate`

2. Change into the directory of the source that you want to run the patch script against.

3. Run the script

    `scripts/patch_appy/apply.py <name of patch file>`

    The script can be run with the `--help` command line option to
    show other available options.


## Running Tests

1. Initialize the virtualenv created during the build

    `. ./env/bin/activate`

2. Run the script you want:

    `./tests/test_basic.py`

Alternatively, all tests can be run by using `pytest` and coverage data can be generated as well by using `pytest --cov=scripts`.  Note that you need to install the pytest-cov module in order for coverage data to work.
