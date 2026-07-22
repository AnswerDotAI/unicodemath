# unicodemath

Parse UnicodeMath and AsciiMath, the two main linear (plain-text) math notations, into a common tree, then emit LaTeX or anything else. UnicodeMath is the notation Microsoft Word uses natively for equations (Unicode Technical Note 28), so `∑_(i=1)^n i^2` or `a^2+b^2=√(c^2)` is valid input. AsciiMath is the pure-ASCII cousin: `sum_(i=1)^n i^2`, `AA x in RR x^2>=0`.

The parser is a small Pratt parser, a clean-room Python port of the design of Peter Jipsen's [umath2latex.js](https://math.chapman.edu/~jipsen/unicodemath/). Its LaTeX output byte-matches that reference implementation across the sample set published with it.

## Install

```sh
pip install unicodemath
```

## Use

```python
from unicodemath import parse, to_latex

to_latex(parse('∀x>0 x^a x^b = x^(a+b)'))
# '\\forall x > 0(x^ax^b = x^{a+b})'

to_latex(parse('int_0^oo e^(-x) dx', dialect='asciimath'))
# '\\int_0^\\infty e^{-x}dx'
```

Matrices work in both dialects: UnicodeMath `■(a&b@c&d)` (and `█(...)` for an equation array, which becomes `aligned`), AsciiMath `[[a,b],[c,d]]`.

```python
to_latex(parse('[[a,b],[c,d]]', dialect='asciimath'))
# '\\begin{bmatrix}a&b\\\\c&d\\end{bmatrix}'
```

`prefixform` renders the parse tree in a compact `op(arg,...)` form, useful for checking how an expression was read:

```python
from unicodemath import prefixform
prefixform(parse('|x+y| ≤ |x|+|y|'))
# '≤(|(+(x,y)),+(|(x),|(y)))'
```

## Backends

`parse` returns a tree of `Node` objects, each with `sym` (the source symbol), `kind` (how it was constructed: `infix`, `chain`, `prefixop`, `around`, `matrix`, ...), and children in `arg`, `arg2`, `arg3`. A backend is a function from that tree to a string; `to_latex` is the one included, and dispatches on `kind`. New dialects register a tokenizer in `unicodemath.core.TOKENIZERS`.

## Scope

The goal is the common mathematical core of both notations, not either spec in full. Known gaps: AsciiMath `text()` and accents (`hat`, `vec`, ...) are not supported, and greedy tokenizing means multi-letter names the symbol table doesn't know (like `sinh`) parse as juxtaposed letters. UnicodeMath control words (`\alpha` style) pass through as literal LaTeX names.

## Development

Version lives in `unicodemath/__init__.py` as `__version__`; release uses fastship (`ship-bump`, `ship-gh`, `ship-pypi`). Tests: `pytest -q`. The Jipsen sample fixtures in `tests/fixtures/` were generated one time from the reference JS and are the port contract: our output must byte-match them.
