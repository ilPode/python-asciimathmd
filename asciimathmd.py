#    Copyright (c) 2014, Davide Poderini
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re, markdown

Element = markdown.util.etree.Element
AtomicString = markdown.util.AtomicString
tostring = markdown.util.etree.tostring

# Alternate syntax
#MATH_DEL = r'(?<![{(\-\[]):(?![}\)\.])' # match :math: avoiding symbols ':.' '{:' '(:' ':)' ':}' '-:' '[:'
#BLOCK_RE = r'(?:^|\n)\[:(\w*)\]' # [:ref] math
#EQREF_RE = r'\[:(\w+)\]' # blah blah [:ref] blah

MATH_DEL = r'((?<![~|\[])~(?![~=|]))' # match ~math~ avoiding '~~' '~=' '~|' '|~' '[~'
BLOCK_RE = r'(?:^|\n)\[~(\w*)\]' # [~ref] math
EQREF_RE = r'\[~(\w+)\]' # blah blah [~ref] blah

LINEBREAK_RE = r'  \n'
NOBREAK_RE = r'(?!.*' + LINEBREAK_RE + '.*)'
INLINEMATH_RE = MATH_DEL + NOBREAK_RE + r'(.*?)' + MATH_DEL

class ASCIIMathMLExtension(markdown.extensions.Extension):
    def __init__(self, configs, **kwargs):
        self.config = {'level_num'  : [1, "Maximum header level to be numbered, from 0 to 6, -1 means no numbering."],
                       'header_num' : [True, "Show number next to header."] }
        super(ASCIIMathMLExtension, self).__init__(**kwargs)
        self.reset()

    def extendMarkdown(self, md, md_globals):
        self.md = md
        
        md.ESCAPED_CHARS.append('~')
        md.parser.blockprocessors.add('block_asciimath', ASCIIMathMLProcessor(md.parser, self), '>code')
        md.treeprocessors.add("eq_number", EqNumberTreeProcessor(self), '<inline')
        md.inlinePatterns.add("eq_reference", EqrefPattern(EQREF_RE, self), '<reference')
        md.inlinePatterns.add('inline_asciimath', ASCIIMathMLPattern(INLINEMATH_RE), '>escape')

    def addEqref(self, ref, num):
        if not ref in self.eqrefDict and ref != '':
            self.eqrefDict[ref] = num 
            return True
        return False

    def makeEqrefId(self, ref):
        return 'eq:'+ref

    def reset(self):
        self.eqrefDict = {}
        
class ASCIIMathMLProcessor(markdown.blockprocessors.BlockProcessor):
    """ Process Block ASCIIMathML. """

    def __init__(self, parser, extension) :
        super(ASCIIMathMLProcessor, self).__init__(parser)
        self.ext = extension
        self.blockRe = re.compile(BLOCK_RE)

    def test(self, parent, block):
        return bool(self.blockRe.search(block))

    def run(self, parent, blocks):
        block = blocks.pop(0)
        msplit = self.blockRe.split(block) 
        if len(msplit) > 1 :
            # Pass the rest of the block to the parser
            before = msplit.pop(0)  # Lines before the math block
            self.parser.parseBlocks(parent, [before])

            eqs = []
            while msplit != [] :
                eqs.append((msplit.pop(0), re.split(LINEBREAK_RE, msplit.pop(0))))
            # If there's only one unlabeled equation we don't need a <mtable> element
            if len(eqs) > 1 or eqs[0][0] != '':
                eqsnode = El('mtable', columalign='left')
                for eq in eqs:
                    eqnode = parse_multiline(*eq[1])
                    if self.ext.addEqref(eq[0],''):
                        eqsnode.append( El('mtr', 
                                        El('mtd', eqnode ), 
                                        El('mtd', El('mtext', text = "(%d)" % (len(self.ext.eqrefDict)), attrib={'class':'eqnum'}), columalign='right') 
                                        , attrib={'id':self.ext.makeEqrefId(eq[0]), 'class':'equation'}) )
                    else:
                        eqsnode.append(El('mtr', eqnode))
            else: 
                eqsnode = parse_multiline(*eqs[0][1])

        mathml = El('math', El('mstyle', eqsnode))
        mathml.set('xmlns', 'http://www.w3.org/1998/Math/MathML')
        mathml.set('display', 'block')
        parent.append(mathml)

class EqrefPattern(markdown.inlinepatterns.Pattern):

    def __init__(self, pattern, extension):
        super(EqrefPattern, self).__init__(pattern)
        self.ext = extension

    def handleMatch(self, m):
        ref = m.group(2)
        if ref in self.ext.eqrefDict:
            a = Element("a")
            a.set('href', '#' + self.ext.makeEqrefId(ref))
            a.set('class', 'eqref')
            a.text = '(' + self.ext.eqrefDict[ref] + ')'
            return a
        else:
            return None

class EqNumberTreeProcessor(markdown.treeprocessors.Treeprocessor):
    """ Climbs the element tree to assign numbers to headers and equations """

    def __init__(self, extension):
        self.ext = extension
        self.maxLevel = min(self.ext.getConfig('level_num'), 6)
        # Initialize counters
        self.counter = [0 for i in range(self.maxLevel+1)] 
        self.eqCount = 0

    def makeNumber(self, level=None):
        """ returns number for header or equation
            level = None -> equations numering
            level = 0 -> h1
            level = 1 -> h2
            level = 2 -> h3
            ...
        """
        c = self.counter.copy()
        while c.count(0) != 0:
            c.remove(0)
        i = (self.maxLevel + 1) if (level is None) else (min(self.maxLevel, level) + 1)
        c = map(str, c[:i])
        num = '.'.join(c)
        if level is None:
            num += '.' + str(self.eqCount)          
        return num

    def stepCounter(self, level=None, step=1):
        """ Update counters """
        if level is None:
            self.eqCount += step
        else:
            l = min(self.maxLevel, level)
            self.counter[l] += step
            for i in range(l+1, self.maxLevel):
                self.counter[i] = 0
            self.eqCount = 0

    def run(self, root):
        # If maxLevel is < 0 the numbering is disabled
        if  self.maxLevel >= 0 :
            headerRe = re.compile(r'[Hh]([1-'+ str(self.maxLevel+1) + '])') 
            refRe = re.compile(r'^eq:(.*)$')
            # Tree climbing
            for e in root.getiterator() :
                mh = headerRe.match(e.tag)
                # Is an header
                if mh:
                    mLevel = int(mh.group(1)) - 1
                    self.stepCounter(level=mLevel) 
                    e.text = self.makeNumber(mLevel) + ' ' + e.text
                
                # Is an equation
                if e.tag == 'mtr' and 'class' in e.attrib and e.attrib['class'] == 'equation':
                    mref = refRe.match(e.attrib['id'])
                    # Ignore it if it's not in the reference dictionary
                    if mref and mref.group(1) in self.ext.eqrefDict:
                        self.stepCounter()
                        numStr = self.makeNumber()
                        self.ext.eqrefDict[mref.group(1)] = numStr
                        # Find and update the number next to the equation
                        for t in e.getiterator('mtext'):
                            if 'class' in t.attrib and t.attrib['class'] == 'eqnum':
                                t.text = '(' + numStr + ')'
                                break

class ASCIIMathMLPattern(markdown.inlinepatterns.Pattern):

    def handleMatch(self, m):
        mathml = parse(m.group(3).strip())
        mathml.set('xmlns', 'http://www.w3.org/1998/Math/MathML')
        return mathml

def makeExtension(configs=None):
    return ASCIIMathMLExtension(configs=configs)

# Parser #

def parse_multiline(*lines) :
    if len(lines) > 1: 
        node = El('mtable', columalign='left')
        for line in lines :
            line, linenodes = parse_exprs(line)
            remove_invisible(linenodes)
            linenodes = map(remove_private, linenodes)
            node.append(El('mtr', *linenodes))
        return node
    elif len(lines) == 1 :
        line, linenodes = parse_exprs(lines[0])
        remove_invisible(linenodes)
        linenodes = map(remove_private, linenodes)
        return El('mrow', *linenodes)
    else:
        return None

def El(tag, text=None, *children, **attrib):
    element = Element(tag, **attrib)

    if not text is None:
        if isinstance(text, str):
            element.text = AtomicString(text)
        else:
            children = (text, ) + children

    for child in children:
        element.append(child)

    return element

number_re = re.compile('-?(\d+\.(\d+)?|\.?\d+)')

def strip_parens(n):
    if n.tag == 'mrow':
        if n[0].get('_opening', False):
           del n[0]

        if n[-1].get('_closing', False):
            del n[-1]

    return n

def is_enclosed_in_parens(n):
    return n.tag == 'mrow' and n[0].get('_opening', False) and n[-1].get('_closing', False)

def binary(operator, operand_1, operand_2, swap=False):
    operand_1 = strip_parens(operand_1)
    operand_2 = strip_parens(operand_2)
    if not swap:
        operator.append(operand_1)
        operator.append(operand_2)
    else:
        operator.append(operand_2)
        operator.append(operand_1)

    return operator

def unary(operator, operand, swap=False):
    operand = strip_parens(operand)
    if swap:
        operator.insert(0, operand)
    else:
        operator.append(operand)

    return operator

def frac(num, den):
    return El('mfrac', strip_parens(num), strip_parens(den))

def sub(base, subscript):
    subscript = strip_parens(subscript)

    if base.tag in ('msup', 'mover'):
        children = base.getchildren()
        n = El('msubsup' if base.tag == 'msup' else 'munderover', children[0], subscript, children[1])
    else:
        n = El('munder' if base.get('_underover', False) else 'msub', base, subscript)

    return n

def sup(base, superscript):
    superscript = strip_parens(superscript)

    if base.tag in ('msub', 'munder'):
        children = base.getchildren()
        n = El('msubsup' if base.tag == 'msub' else 'munderover', children[0], children[1], superscript)
    else:
        n = El('mover' if base.get('_underover', False) else 'msup', base, superscript)

    return n

def parse(s):
    """
Translates from ASCIIMathML (an easy to type and highly readable way to
represent math formulas) into MathML (a w3c standard directly displayable by
some web browsers).

The function `parse()` generates a tree of elements:

    >>> import asciimathml
    >>> asciimathml.parse('sqrt 2')
    <Element math at b76fb28c>

The tree can then be manipulated using the standard python library.  For
example we can generate its string representation:

    >>> from xml.etree.ElementTree import tostring
    >>> tostring(asciimathml.parse('sqrt 2'))
    '<math><mstyle><msqrt><mn>2</mn></msqrt></mstyle></math>'
    """
    s, nodes = parse_exprs(s)
    remove_invisible(nodes)
    nodes = map(remove_private, nodes)

    return El('math', El('mstyle', *nodes))

delimiters = {'{': '}', '(': ')', '[': ']'}

def parse_string(s):
    opening = s[0]

    if opening in delimiters:
        closing = delimiters[opening]
        end = s.find(closing)

        text = s[1:end]
        s = s[end+1:]
    else:
        s, text = parse_m(s)

    return s, El('mrow', El('mtext', text))

tracing_level = 0
def trace_parser(p):
    """
    Decorator for tracing the parser.

    Use it to decorate functions with signature:

      string -> (string, nodes)

    and a trace of the progress made by the parser will be printed to stderr.

    Currently parse_exprs(), parse_expr() and parse_m() have the right signature.
    """

    def nodes_to_string(n):
        if isinstance(n, list):
            result = '[ '
            for m in map(nodes_to_string, n):
                result += m
                result += ' '
            result += ']'

            return result
        else:
            try:
                return tostring(remove_private(copy(n)))
            except Exception as e:
                return n

    def print_trace(*args):
        import sys

        sys.stderr.write("    " * tracing_level)
        for arg in args:
            sys.stderr.write(str(arg))
            sys.stderr.write(' ')
        sys.stderr.write('\n')
        sys.stderr.flush()

    def wrapped(s, *args, **kwargs):
        global tracing_level

        print_trace(p.__name__, repr(s))

        tracing_level += 1
        s, n = p(s, *args, **kwargs)
        tracing_level -= 1

        print_trace("-> ", repr(s), nodes_to_string(n))

        return s, n

    return wrapped

def parse_expr(s, siblings, required=False):
    s, n = parse_m(s, required=required)

    if not n is None:
        # Being both an _opening and a _closing element is a trait of
        # symmetrical delimiters (e.g. ||).
        # In that case, act as an opening delimiter only if there is not
        # already one of the same kind among the preceding siblings.
        if n.get('_opening', False) \
           and (not n.get('_closing', False) \
                or find_node_backwards(siblings, n.text) == -1):
            s, children = parse_exprs(s, [n], inside_parens=True)
            n = El('mrow', *children)

        if n.tag == 'mtext':
            s, n = parse_string(s)
        elif n.get('_arity', 0) == 1:
            s, m = parse_expr(s, [], True)
            n = unary(n, m, n.get('_swap', False))
        elif n.get('_arity', 0) == 2:
            s, m1 = parse_expr(s, [], True)
            s, m2 = parse_expr(s, [], True)
            n = binary(n, m1, m2, n.get('_swap', False))

    return s, n

def find_node(ns, text):
    for i, n in enumerate(ns):
        if n.text == text:
            return i

    return -1

def find_node_backwards(ns, text):
    for i, n in enumerate(reversed(ns)):
        if n.text == text:
            return len(ns) - i

    return -1

def nodes_to_row(row):
    mrow = El('mtr')

    nodes = row.getchildren()

    while True:
        i = find_node(nodes, ',')

        if i > 0:
            mrow.append(El('mtd', *nodes[:i]))

            nodes = nodes[i+1:]
        else:
            mrow.append(El('mtd', *nodes))
            break

    return mrow

def nodes_to_matrix(nodes):
    mtable = El('mtable')

    for row in nodes[1:-1]:
        if row.text == ',':
            continue

        mtable.append(nodes_to_row(strip_parens(row)))

    return El('mrow', nodes[0], mtable, nodes[-1])

def parse_exprs(s, nodes=None, inside_parens=False):
    if nodes is None:
        nodes = []

    inside_matrix = False

    while True:
        s, n = parse_expr(s, nodes)

        if not n is None:
            nodes.append(n)

            if n.get('_closing', False):
                if not inside_matrix:
                    return s, nodes
                else:
                    return s, nodes_to_matrix(nodes)

            if inside_parens and n.text == ',' and is_enclosed_in_parens(nodes[-2]):
                inside_matrix = True

            if len(nodes) >= 3 and nodes[-2].get('_special_binary'):
                transform =  nodes[-2].get('_special_binary')
                nodes[-3:] = [transform(nodes[-3], nodes[-1])]

        if s == '':
            return '', nodes

def remove_private(n):
    _ks = [k for k in n.keys() if k.startswith('_') or k == 'attrib']

    for _k in _ks:
        del n.attrib[_k]

    for c in n.getchildren():
        remove_private(c)

    return n

def remove_invisible(ns):
    for i in range(len(ns)-1, 0, -1):
        if ns[i].get('_invisible', False):
            del ns[i]
        else:
            remove_invisible(ns[i].getchildren())

def copy(n):
    m = El(n.tag, n.text, **dict(n.items()))

    for c in n.getchildren():
        m.append(copy(c))

    return m

def parse_m(s, required=False):
    s = s.strip()

    if s == '':
        return '', El('mi', '\u25a1') if required else None

    m = number_re.match(s)

    if m:
        number = m.group(0)
        if number[0] == '-':
            return s[m.end():], El('mrow', El('mo', '-'), El('mn', number[1:]))
        else:
            return s[m.end():], El('mn', number)

    for y in symbol_names:
        if s.startswith(y):
            n = copy(symbols[y])

            if n.get('_space', False):
                n = El('mrow',
                        El('mspace', width='1ex'),
                        n,
                        El('mspace', width='1ex'))

            return s[len(y):], n

    return s[1:], El('mi' if s[0].isalpha() else 'mo', s[0])

symbols = {}

def Symbol(input, el):
    symbols[input] = el

Symbol(input="alpha",  el=El("mi", "\u03B1"))
Symbol(input="beta",  el=El("mi", "\u03B2"))
Symbol(input="chi",    el=El("mi", "\u03C7"))
Symbol(input="delta",  el=El("mi", "\u03B4"))
Symbol(input="Delta",  el=El("mo", "\u0394"))
Symbol(input="epsi",   el=El("mi", "\u03B5"))
Symbol(input="varepsilon", el=El("mi", "\u025B"))
Symbol(input="eta",    el=El("mi", "\u03B7"))
Symbol(input="gamma",  el=El("mi", "\u03B3"))
Symbol(input="Gamma",  el=El("mo", "\u0393"))
Symbol(input="iota",   el=El("mi", "\u03B9"))
Symbol(input="kappa",  el=El("mi", "\u03BA"))
Symbol(input="lambda", el=El("mi", "\u03BB"))
Symbol(input="Lambda", el=El("mo", "\u039B"))
Symbol(input="mu",     el=El("mi", "\u03BC"))
Symbol(input="nu",     el=El("mi", "\u03BD"))
Symbol(input="omega",  el=El("mi", "\u03C9"))
Symbol(input="Omega",  el=El("mo", "\u03A9"))
Symbol(input="phi",    el=El("mi", "\u03C6"))
Symbol(input="varphi", el=El("mi", "\u03D5"))
Symbol(input="Phi",    el=El("mo", "\u03A6"))
Symbol(input="pi",     el=El("mi", "\u03C0"))
Symbol(input="Pi",     el=El("mo", "\u03A0"))
Symbol(input="psi",    el=El("mi", "\u03C8"))
Symbol(input="Psi",    el=El("mi", "\u03A8"))
Symbol(input="rho",    el=El("mi", "\u03C1"))
Symbol(input="sigma",  el=El("mi", "\u03C3"))
Symbol(input="Sigma",  el=El("mo", "\u03A3"))
Symbol(input="tau",    el=El("mi", "\u03C4"))
Symbol(input="theta",  el=El("mi", "\u03B8"))
Symbol(input="vartheta", el=El("mi", "\u03D1"))
Symbol(input="Theta",  el=El("mo", "\u0398"))
Symbol(input="upsilon", el=El("mi", "\u03C5"))
Symbol(input="xi",     el=El("mi", "\u03BE"))
Symbol(input="Xi",     el=El("mo", "\u039E"))
Symbol(input="zeta",   el=El("mi", "\u03B6"))

Symbol(input="*",  el=El("mo", "\u22C5"))
Symbol(input="**", el=El("mo", "\u22C6"))

Symbol(input="/", el=El("mo", "/", _special_binary=frac))
Symbol(input="^", el=El("mo", "^", _special_binary=sup))
Symbol(input="_", el=El("mo", "_", _special_binary=sub))
Symbol(input="//", el=El("mo", "/"))
Symbol(input="\\\\", el=El("mo", "\\"))
Symbol(input="setminus", el=El("mo", "\\"))
Symbol(input="xx", el=El("mo", "\u00D7"))
Symbol(input="-:", el=El("mo", "\u00F7"))
Symbol(input="@",  el=El("mo", "\u2218"))
Symbol(input="o+", el=El("mo", "\u2295"))
Symbol(input="ox", el=El("mo", "\u2297"))
Symbol(input="o.", el=El("mo", "\u2299"))
Symbol(input="sum", el=El("mo", "\u2211", _underover=True))
Symbol(input="prod", el=El("mo", "\u220F", _underover=True))
Symbol(input="^^",  el=El("mo", "\u2227"))
Symbol(input="^^^", el=El("mo", "\u22C0", _underover=True))
Symbol(input="vv",  el=El("mo", "\u2228"))
Symbol(input="vvv", el=El("mo", "\u22C1", _underover=True))
Symbol(input="nn",  el=El("mo", "\u2229"))
Symbol(input="nnn", el=El("mo", "\u22C2", _underover=True))
Symbol(input="uu",  el=El("mo", "\u222A"))
Symbol(input="uuu", el=El("mo", "\u22C3", _underover=True))

Symbol(input="!=",  el=El("mo", "\u2260"))
Symbol(input=":=",  el=El("mo", ":="))
Symbol(input="lt",  el=El("mo", "<"))
Symbol(input="<=",  el=El("mo", "\u2264"))
Symbol(input="lt=", el=El("mo", "\u2264"))
Symbol(input=">=",  el=El("mo", "\u2265"))
Symbol(input="geq", el=El("mo", "\u2265"))
Symbol(input="-<",  el=El("mo", "\u227A"))
Symbol(input="-lt", el=El("mo", "\u227A"))
Symbol(input=">-",  el=El("mo", "\u227B"))
Symbol(input="-<=", el=El("mo", "\u2AAF"))
Symbol(input=">-=", el=El("mo", "\u2AB0"))
Symbol(input="in",  el=El("mo", "\u2208"))
Symbol(input="!in", el=El("mo", "\u2209"))
Symbol(input="sub", el=El("mo", "\u2282"))
Symbol(input="sup", el=El("mo", "\u2283"))
Symbol(input="sube", el=El("mo", "\u2286"))
Symbol(input="supe", el=El("mo", "\u2287"))
Symbol(input="-=",  el=El("mo", "\u2261"))
Symbol(input="~=",  el=El("mo", "\u2245"))
Symbol(input="~~",  el=El("mo", "\u2248"))
Symbol(input="prop", el=El("mo", "\u221D"))

Symbol(input="and", el=El("mtext", "and", _space=True))
Symbol(input="or",  el=El("mtext", "or", _space=True))
Symbol(input="not", el=El("mo", "\u00AC"))
Symbol(input="=>",  el=El("mo", "\u21D2"))
Symbol(input="if",  el=El("mo", "if", _space=True))
Symbol(input="<=>", el=El("mo", "\u21D4"))
Symbol(input="AA",  el=El("mo", "\u2200"))
Symbol(input="EE",  el=El("mo", "\u2203"))
Symbol(input="_|_", el=El("mo", "\u22A5"))
Symbol(input="TT",  el=El("mo", "\u22A4"))
Symbol(input="|--",  el=El("mo", "\u22A2"))
Symbol(input="|==",  el=El("mo", "\u22A8"))

Symbol(input="(",  el=El("mo", "(", _opening=True))
Symbol(input=")",  el=El("mo", ")", _closing=True))
Symbol(input="[",  el=El("mo", "[", _opening=True))
Symbol(input="]",  el=El("mo", "]", _closing=True))
Symbol(input="{",  el=El("mo", "{", _opening=True))
Symbol(input="}",  el=El("mo", "}", _closing=True))
Symbol(input="|", el=El("mo", "|", _opening=True, _closing=True))
Symbol(input="||", el=El("mo", "\u2016", _opening=True, _closing=True)) # double vertical line
Symbol(input="(:", el=El("mo", "\u2329", _opening=True))
Symbol(input=":)", el=El("mo", "\u232A", _closing=True))
Symbol(input="<<", el=El("mo", "\u2329", _opening=True))
Symbol(input=">>", el=El("mo", "\u232A", _closing=True))
Symbol(input="{:", el=El("mo", "{:", _opening=True, _invisible=True))
Symbol(input=":}", el=El("mo", ":}", _closing=True, _invisible=True))

Symbol(input="int",  el=El("mo", "\u222B"))
# Symbol(input="dx",   el=El("mi", "{:d x:}", _definition=True))
# Symbol(input="dy",   el=El("mi", "{:d y:}", _definition=True))
# Symbol(input="dz",   el=El("mi", "{:d z:}", _definition=True))
# Symbol(input="dt",   el=El("mi", "{:d t:}", _definition=True))
Symbol(input="oint", el=El("mo", "\u222E"))
Symbol(input="del",  el=El("mo", "\u2202"))
Symbol(input="grad", el=El("mo", "\u2207"))
Symbol(input="+-",   el=El("mo", "\u00B1"))
Symbol(input="O/",   el=El("mo", "\u2205"))
Symbol(input="oo",   el=El("mo", "\u221E"))
Symbol(input="aleph", el=El("mo", "\u2135"))
Symbol(input="...",  el=El("mo", "..."))
Symbol(input=":.",  el=El("mo", "\u2234"))
Symbol(input="/_",  el=El("mo", "\u2220"))
Symbol(input="\\ ",  el=El("mo", "\u00A0"))
Symbol(input="quad", el=El("mo", "\u00A0\u00A0"))
Symbol(input="qquad", el=El("mo", "\u00A0\u00A0\u00A0\u00A0"))
Symbol(input="cdots", el=El("mo", "\u22EF"))
Symbol(input="vdots", el=El("mo", "\u22EE"))
Symbol(input="ddots", el=El("mo", "\u22F1"))
Symbol(input="diamond", el=El("mo", "\u22C4"))
Symbol(input="square", el=El("mo", "\u25A1"))
Symbol(input="|__", el=El("mo", "\u230A"))
Symbol(input="__|", el=El("mo", "\u230B"))
Symbol(input="|~", el=El("mo", "\u2308"))
Symbol(input="~|", el=El("mo", "\u2309"))
Symbol(input="CC",  el=El("mo", "\u2102"))
Symbol(input="NN",  el=El("mo", "\u2115"))
Symbol(input="QQ",  el=El("mo", "\u211A"))
Symbol(input="RR",  el=El("mo", "\u211D"))
Symbol(input="ZZ",  el=El("mo", "\u2124"))
Symbol(input="f",   el=El("mi", "f", _func=True)) # sample
Symbol(input="g",   el=El("mi", "g", _func=True))

Symbol(input="lim",  el=El("mo", "lim", _underover=True))
Symbol(input="Lim",  el=El("mo", "Lim", _underover=True))
Symbol(input="sin",  el=El("mrow", El("mo", "sin"), _arity=1))
Symbol(input="sin",  el=El("mrow", El("mo", "sin"), _arity=1))
Symbol(input="cos",  el=El("mrow", El("mo", "cos"), _arity=1))
Symbol(input="tan",  el=El("mrow", El("mo", "tan"), _arity=1))
Symbol(input="sinh", el=El("mrow", El("mo", "sinh"), _arity=1))
Symbol(input="cosh", el=El("mrow", El("mo", "cosh"), _arity=1))
Symbol(input="tanh", el=El("mrow", El("mo", "tanh"), _arity=1))
Symbol(input="cot",  el=El("mrow", El("mo", "cot"), _arity=1))
Symbol(input="sec",  el=El("mrow", El("mo", "sec"), _arity=1))
Symbol(input="csc",  el=El("mrow", El("mo", "csc"), _arity=1))
Symbol(input="log",  el=El("mrow", El("mo", "log"), _arity=1))
Symbol(input="ln",   el=El("mrow", El("mo", "ln"), _arity=1))
Symbol(input="det",  el=El("mrow", El("mo", "det"), _arity=1))
Symbol(input="gcd",  el=El("mrow", El("mo", "gcd"), _arity=1))
Symbol(input="lcm",  el=El("mrow", El("mo", "lcm"), _arity=1))
Symbol(input="dim",  el=El("mo", "dim"))
Symbol(input="mod",  el=El("mo", "mod"))
Symbol(input="lub",  el=El("mo", "lub"))
Symbol(input="glb",  el=El("mo", "glb"))
Symbol(input="min",  el=El("mo", "min", _underover=True))
Symbol(input="max",  el=El("mo", "max", _underover=True))

Symbol(input="uarr", el=El("mo", "\u2191"))
Symbol(input="darr", el=El("mo", "\u2193"))
Symbol(input="rarr", el=El("mo", "\u2192"))
Symbol(input="->",   el=El("mo", "\u2192"))
Symbol(input="|->",  el=El("mo", "\u21A6"))
Symbol(input="larr", el=El("mo", "\u2190"))
Symbol(input="harr", el=El("mo", "\u2194"))
Symbol(input="rArr", el=El("mo", "\u21D2"))
Symbol(input="lArr", el=El("mo", "\u21D0"))
Symbol(input="hArr", el=El("mo", "\u21D4"))

Symbol(input="hat", el=El("mover", El("mo", "\u005E"), _arity=1, _swap=1))
Symbol(input="bar", el=El("mover", El("mo", "\u00AF"), _arity=1, _swap=1))
Symbol(input="vec", el=El("mover", El("mo", "\u2192"), _arity=1, _swap=1))
Symbol(input="dot", el=El("mover", El("mo", "."), _arity=1, _swap=1))
Symbol(input="ddot",el=El("mover", El("mo", ".."), _arity=1, _swap=1))
Symbol(input="ul", el=El("munder", El("mo", "\u0332"), _arity=1, _swap=1))

Symbol(input="sqrt", el=El("msqrt", _arity=1))
Symbol(input="root", el=El("mroot", _arity=2, _swap=True))
Symbol(input="frac", el=El("mfrac", _arity=2))
Symbol(input="stackrel", el=El("mover", _arity=2))

Symbol(input="text", el=El("mtext", _arity=1))
# {input:"mbox", tag:"mtext", output:"mbox", tex:null, ttype:TEXT},
# {input:"\"",   tag:"mtext", output:"mbox", tex:null, ttype:TEXT};

symbol_names = sorted(symbols.keys(), key=lambda s: len(s), reverse=True)
