# boilerplate

A small utility which is used to add the boilerplate text containing copyright and license information at the top of source files. To ensure that paths are emitted correctly it should always be run from the project’s root directory. As well as the boilerplate program itself, the `all.py` utility provides a convenient way of updating all of the header and source files within the directory hierarchy of a project.

By default, `boilerplate.py` uses the [pyfiglet](https://github.com/pwaller/pyfiglet) library to generate banner text. If not available, this feature can be disabled.
