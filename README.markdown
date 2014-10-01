ASCIIMathML Markdown
====================

Work in progress
-----------------
This is Pre-alpha code. Be careful, it bites. 

Description
-----------
Extension to [Python Markdown][python-markdown] for [ASCIIMathML][] support. 
This extension adds inline and block math and equation numbering with references.

The parsing code is entirely copied from [here][python-asciimathml], the only thing I did is adding the math block syntax.

Usage
------
To add inline math to your text enclose it in `::` :
    
    blah blah :: e^(ix) = cos(x) + i sin(x) :: blah blah

To start a math block put a '[:ref]' at the beginning of the line, and end it with a blank line.
In a math block a '::' will be interpreted as a line break.
You can reference an equation in the text with '[:ref]' (for obvious reasons you can't do this at the beginning of a line).

    blah blah
    [:1] e^(ix) = cos(x) + i sin(x)
    ::  cos(x) = (e^(ix) + e^(-ix))/2
        sin(x) = (e^(ix) - e^(-ix))/(2i)

    I love equation [:1].

Help
----
If you have any ideas for a better syntax let me know. 

[ASCIIMathML]: http://www1.chapman.edu/~jipsen/mathml/asciimath.html
[etree]: http://docs.python.org/library/xml.etree.elementtree.html
[python-markdown]: http://www.freewisdom.org/projects/python-markdown/
[python-asciimathml]: https://github.com/favalex/python-asciimathml
