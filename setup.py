# Copyright (c) 2014, Davide Poderini
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup
setup(
    name = "asciimathmd",
    py_modules = ["asciimathmd"],
    version = "0.1",
    description = "ASCIIMathML Extension for Python Markdown",
    author = "Davide Poderini",
    author_email = "spapode@gmail.com",
    url = "http://github.com/ilpode/python-mdasciimathmd",
    keywords = ["markup", "math", "mathml", "markdown"],
    classifiers = [
        "Programming Language :: Python",
        "Development Status ::  2 - Pre-Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: XML"
        ],
    long_description = """Extension to Python Markdown for ASCIIMathML that adds inline and block math support with equation referencing"""
)
