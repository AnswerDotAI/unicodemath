"Emit LaTeX from a parsed linear-math `Node` tree, matching the reference converter byte-for-byte"

__all__ = ['to_latex']

def _wrap(sub, t, brace=False):
    if (sub.bp > t.bp or sub.arg is None or sub.arg == []
        or (sub.sym == t.sym and isinstance(t.arg, list) and len(t.arg) == 1)): return to_latex(sub)
    if brace: return '{' + to_latex(sub) + '}'
    st = to_latex(sub)
    return st if st[:1] == '[' else '(' + st + ')'

def _isalpha(c): return 'a' <= c <= 'z' or 'A' <= c <= 'Z'

def _atom(t):
    if t.tex: return t.tex + ' ' if t.tex[0] == '\\' else t.tex
    if t.sym[0] == '\\': return t.sym + ' '
    return '\\' + t.sym if len(t.sym) > 1 and _isalpha(t.sym[0]) else t.sym

def _funcapp(t):
    st = _wrap(t.arg, t)
    fl = st[:1] in ('(', '[')
    return t.tex + ('' if fl else '(') + st + ('' if fl else ')')

def _infix(t): return _wrap(t.arg, t) + t.tex + (' ' if t.tex[0] == '\\' else '') + _wrap(t.arg2, t)

def _infixr(t):
    if t.sym in ('^', '_'): return _wrap(t.arg, t) + t.tex + _wrap(t.arg2, t, True)
    s1 = ' ' if t.bp < 50 else ''
    s2 = ' ' if t.bp < 50 or t.tex[0] == '\\' else ''
    return _wrap(t.arg, t) + s1 + t.tex + s2 + _wrap(t.arg2, t)

def _chain(t):
    st = t.tex if not t.arg else _wrap(t.arg[0], t)
    if t.sym == '\\,':
        for i, x in enumerate(t.arg[1:], 1):
            if i == len(t.arg)-1 and x.arg3 is not None: st += ' ' + to_latex(x)
            else: st += _wrap(x, t)
        return st
    s1 = ' ' if t.bp < 50 and t.sym != ',' else ''
    s2 = ' ' if (t.bp < 50 or t.tex[0] == '\\') and t.sym != ',' else ''
    for x in t.arg[1:]: st += s1 + t.tex + s2 + _wrap(x, t)
    return st

def _abschain(t):
    st = _wrap(t.arg[0], t)
    for i, x in enumerate(t.arg[1:], 1):
        if i == len(t.arg)-1 and x.arg3 is not None: st += ' ' + to_latex(x)
        else: st += ' ' + _wrap(x, t)
    return st

def _absr(t): return '|' + to_latex(t.arg) + '|'
def _postfix(t): return _wrap(t.arg, t) + t.tex
def _prefix(t): return t.tex + ' ' + _wrap(t.arg, t)
def _minus(t): return t.tex + _wrap(t.arg, t)

def _prefixop(t):
    return (t.tex + ('_' + _wrap(t.arg, t, True) if t.arg is not None else '')
        + ('^' + _wrap(t.arg2, t, True) if t.arg2 is not None else ' ') + _wrap(t.arg3, t))

def _around(t): return t.tex + to_latex(t.arg) + t.entry.texr

def _quant(t):
    nxt = t.arg2.sym in ('∀', '∃')
    return t.tex + ' ' + to_latex(t.arg) + ('' if nxt else '(') + to_latex(t.arg2) + ('' if nxt else ')')

def _setb(t):
    if t.arg2 is not None: return '\\{' + to_latex(t.arg) + ' \\mid ' + to_latex(t.arg2) + '\\}'
    return '\\{' + ', '.join(to_latex(x) for x in t.arg) + '\\}'

def _sqrt(t): return '\\sqrt' + ('[' + to_latex(t.arg2) + ']' if t.arg2 is not None else '') + '{' + to_latex(t.arg) + '}'

def _bracket(t): return '[' + to_latex(t.arg) + ']'

def _frac(t): return '\\frac{' + to_latex(t.arg) + '}{' + to_latex(t.arg2) + '}'
def _root(t): return '\\sqrt[' + to_latex(t.arg) + ']{' + to_latex(t.arg2) + '}'
def _stackrel(t): return '\\stackrel{' + to_latex(t.arg) + '}{' + to_latex(t.arg2) + '}'
def _mrow(t): return '&'.join(to_latex(x) for x in t.arg)
def _matrix(t): return '\\begin{' + t.tex + '}' + '\\\\'.join(to_latex(r) for r in t.arg) + '\\end{' + t.tex + '}'
def _amlist(t): return '[' + ','.join(to_latex(x) for x in t.arg) + ']'

_emit = dict(atom=_atom, funcapp=_funcapp, infix=_infix, infixr=_infixr, chain=_chain, abschain=_abschain, absr=_absr, postfix=_postfix, prefix=_prefix,
    minus=_minus, prefixop=_prefixop, around=_around, quant=_quant, setb=_setb, sqrt=_sqrt, bracket=_bracket, frac=_frac, root=_root,
    stackrel=_stackrel, mrow=_mrow, matrix=_matrix, amlist=_amlist)

def to_latex(t):
    "Emit `t` (from `parse`) as LaTeX"
    return _emit[t.kind](t)
