ASCIIMathML Markdown
====================

Work in progress
-----------------
This is Pre-alpha code. Be careful, it bites. 

Description
-----------
Extension for [Python Markdown][python-markdown] wich adds math support in [ASCIIMathML][] syntax. 
This extension provides inline, block math and equation numbering with references.

The parsing code is taken from [here][python-asciimathml], the only thing I did is adding the math block and numbering system.

Usage
------
To add inline math to your text enclose it in `~` :
    
    blah blah ~ e^(ix) = cos(x) + i sin(x) ~ blah blah

To start a math block put a `[~ref]` at the beginning of the line, and end it with a blank line.
In a math block a `~` at the beginning of the line will be interpreted as a line break.
You can reference an equation in the text with `[~ref]`:

    blah blah
    [~1] e^(ix) = cos(x) + i sin(x)
    ~  cos(x) = (e^(ix) + e^(-ix))/2
        sin(x) = (e^(ix) - e^(-ix))/(2i)

    I love equation [~1].

### Configuration ###

The equation reference number can be global (like `(1)`) or preceded by header's number (like in `(1.2.3)`).
You can choose the behaviour using this 2 config parameters:

- level_num : Maximum level of header to keep track of (Default is 1).
    * -1 : No header's number (global equation's number)
    * 0 : Number only on h1
    * 1 : Number on h1 and h2
    ...
- header_num: Wether or not to show the number near the header (Default is True)

Help
----
If you have any ideas for a better syntax let me know.

[ASCIIMathML]: http://www1.chapman.edu/~jipsen/mathml/asciimath.html
[python-markdown]:https://pypi.python.org/pypi/Markdown
[python-asciimathml]: https://github.com/favalex/python-asciimathml
