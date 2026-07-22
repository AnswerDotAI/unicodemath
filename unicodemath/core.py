"""Linear-math parser: UnicodeMath source -> a tree of `Node`s for backends to emit.

A clean-room Python port of the design of Peter Jipsen's umath2latex.js
(math.chapman.edu/~jipsen/unicodemath/), a Pratt/TDOP parser. Each `Node` carries
`sym`, `tex`, `bp`, `kind`, and `arg`/`arg2`/`arg3`; emitters dispatch on `kind`."""

import re
from functools import wraps
from fastcore.utils import *

__all__ = ['parse', 'prefixform', 'ParseError', 'Node']

class ParseError(Exception): pass

class Sym:
    def __init__(self, sym, tex=None, lbp=0, typ=None):
        store_attr()
        self.nudk = self.ledk = self.nbp = self.ledbp = self.closer = self.texr = None

class Node:
    def __init__(self, sym, tex=None, bp=0, typ=None, kind='atom', entry=None, arg=None, arg2=None, arg3=None): store_attr()
    def __repr__(self): return prefixform(self)

_names = 'or ln and lim sin cos tan cot sec csc log gcd lcm det'.split()

def _isalpha(c): return 'a' <= c <= 'z' or 'A' <= c <= 'Z'

def _backslash(toks, s, i):
    i += 1
    c = s[i] if i < len(s) else ''
    if c <= ' ': return i+1
    if c in '{}':
        toks.append((None, '\\'+c))
        return i+1
    j = i
    while j < len(s) and _isalpha(s[j]): j += 1
    toks.append((None, '\\'+s[i:j]))
    return j

def _number(toks, s, i):
    j = i+1
    while j < len(s) and '0' <= s[j] <= '9': j += 1
    if j < len(s) and s[j] == '.':
        j += 1
        while j < len(s) and '0' <= s[j] <= '9': j += 1
    toks.append(('number', s[i:j]))
    return j

def tokenize(s):
    "Token `(typ, sym)` pairs; typ is None, 'number', or 'function'"
    toks,i,n = [],0,len(s)
    while i < n:
        c = s[i]
        if c <= ' ': i += 1
        elif s[i:i+3] in _names or s[i:i+2] in _names:
            t = s[i:i+3] if s[i:i+3] in _names else s[i:i+2]
            toks.append((None, t))
            i += len(t)
        elif (m := re.match(r'[a-zA-Z]{2,}\(', s[i:])):
            t = m[0][:-1]
            if len(t) == 2 and t[0] == 'd': t = 'd'
            toks.append((None if t == 'd' else 'function', t))
            i += len(t)
        elif _isalpha(c):
            toks.append((None, c))
            i += 1
        elif c == '\\': i = _backslash(toks, s, i)
        elif '0' <= c <= '9': i = _number(toks, s, i)
        elif c == '%':
            while i < n and s[i] not in '\n\r': i += 1
        else:
            toks.append((None, c))
            i += 1
    return toks

SYMS = {}

def listable(f):
    "`f` may take a list of tuples as its first arg: each tuple is called as `f(*el, *rest)`"
    @wraps(f)
    def _f(x, *args, **kw): return [f(*o, *args, **kw) for o in x] if isinstance(x, list) else f(x, *args, **kw)
    return _f

@listable
def _symbol(sym, tex=None, lbp=0, typ=None):
    s = SYMS.get(sym)
    if s:
        s.tex = tex
        if lbp >= s.lbp: s.lbp = lbp
    else: s = SYMS[sym] = Sym(sym, tex, lbp, typ)
    return s

@listable
def _constant(sym, tex=None, typ=None):
    s = _symbol(sym, tex, 0, typ)
    s.nudk = 'const'
    return s

@listable
def _infix(sym, tex, bp, ledk='infix'):
    s = _symbol(sym, tex, bp)
    s.ledk,s.ledbp = ledk,bp
    return s

@listable
def _prefix(sym, tex, bp, nudk='prefix'):
    s = _symbol(sym, tex)
    s.nudk,s.nbp = nudk,bp
    return s

@listable
def _aroundfix(l, r, texl, texr, bp):
    s = _symbol(l, texl)
    _symbol(r, texr, -1)
    s.nudk,s.nbp,s.closer,s.texr = 'around',bp,r,texr
    return s

_infixr,_infixchain,_postfix = (partial(_infix, ledk=k) for k in ('infixr', 'chain', 'postfix'))
_prefixop,_quantifier = (partial(_prefix, nudk=k) for k in ('prefixop', 'quant'))

def _specs(lst, same=False): return [(x, '\\'+x) if same else (x[0], '\\'+x[2:]) for x in lst]

_symbol([(')',')'), (']',']'), ('}','}'), ('\\}','\\}'), ('&','&'), ('@','@')], -1)
_prefix('(', '(', 0, 'paren').closer = ')'
_prefix('{', '{', 0, 'paren').closer = '}'
_constant(_specs(['α alpha', 'β beta', 'χ chi', 'δ delta', 'Δ Delta', 'γ gamma', 'Γ Gamma', 'ϵ epsilon', 'ɛ varepsilon', 'η eta', 'ι iota', 'κ kappa',
    'λ lambda', 'Λ Lambda', 'μ mu', 'ν nu', 'ω omega', 'Ω Omega', 'ϕ phi', 'φ varphi', 'Φ Phi', 'π pi', 'Π Pi', 'ψ psi', 'Ψ Psi', 'ρ rho',
    'σ sigma', 'Σ Sigma', 'τ tau', 'θ theta', 'ϑ vartheta', 'Θ Theta', 'υ upsilon', 'ξ xi', 'Ξ Xi', 'ζ zeta']))
_constant(_specs(['ℕ mathbb N', 'ℤ mathbb Z', 'ℚ mathbb Q', 'ℝ mathbb R', 'ℂ mathbb C', '∅ emptyset', '℘ wp', 'ℵ aleph', 'ℶ beth', 'ℑ Im', 'ℜ Re',
    '∠ angle', '⦜ Angle', '⊥ bot', '⊤ top', '✓ checkmark', '♣ clubsuit', '♢ diamondsuit', '♡ heartsuit', '♠ spadesuit', '† dagger', '° degree',
    '… dots', '⋰ adots', '⋯ cdots', '⋱ ddots', '⋮ vdots', 'ℓ ell', '€ euro', '♭ flat', '♯ sharp', '⌢ frown', '⌣ smile', 'ħ hbar', '∞ infty']))
_constant([('f','f'), ('g','g'), ('F','F'), ('G','G')], 'function')
_infixr([('⊢','\\vdash'), ('⊨','\\models')], 10)
_infix([('∣','\\mid'), (':',':')], 15)
_infixr([('⟹','\\implies'), ('⟸','\\impliedby'), ('⟺','\\iff')], 20)
_infixchain([('and','\\text{ and }'), ('or','\\text{ or }')], 30)
_prefix('¬', '\\neg', 35)
_quantifier([('∀','\\forall'), ('∃','\\exists')], 35)
_infixchain([('=','='), ('<','<'), ('>','>')], 40)
_infixchain(_specs(['∈ in', '≠ ne', '≈ approx', '≅ cong', '≡ equiv', '≤ le', '≥ ge', '⊂ subset', '⊆ subseteq', '⊃ supset', '⊇ supseteq', '≯ ngtr',
    '≮ nless', '∤ nmid', '∉ notin', '≺ prec', '⊀ nprec', '⪯ preceq', '≻ succ', '⊁ nsucc', '⪰ succeq', '∥ parallel', '∦ nparallel', '∝ propto',
    '∼ sim', '⊏ sqsubset', '⊑ sqsubseteq', '⊐ sqsupset', '⊒ sqsupseteq']), 40)
_infixr('R', 'R', 40)
_infixchain(',', ',', 45)
_infix([('-','-'), ('+','+')], 50)
_infix(_specs(['∖ setminus', '∪ cup', '∩ cap', '⊎ uplus', '∨ vee', '∧ wedge', '± pm', '⊖ ominus', '⊕ oplus', '⊓ sqcap', '⊔ sqcup', '◃ triangleleft',
    '▹ triangleright']), 50)
_infixchain('→', '\\to', 50)
_prefix([('∁','\\complement'), ('∂','\\partial'), ('∇','\\del')], 50)
_prefixop(_specs(['⋁ bigvee', '⋀ bigwedge', '⋃ bigcup', '⋂ bigcap', '⨄ biguplus', '∑ sum', '∫ int', '∬ iint', '∭ iiint', '∮ oint', '∯ oiint',
    '∰ oiiint', '∐ coprod']), 50)
_prefixop('lim', '\\lim', 50)
_infix(_specs(['⋅ cdot', '∘ circ', '⊙ odot', '⊘ oslash', '⦸ obslash', '⨿ amalg', '⋉ ltimes', '⋊ rtimes', '⋈ bowtie', '⅋ upand', '≀ wr', '÷ div',
    '⊗ otimes']), 60)
_infixchain('×', '\\times', 60)
_infix([('*','*'), ('/','/')], 60)
_prefixop('∏', '\\prod', 60)
_prefix([('◊','\\lozenge'), ('□','\\square')], 65)
_prefix(_specs('sin cos tan cot sec csc ln gcd lcm det div mod'.split(), same=True), 70)
_prefix(_specs(['↓ downarrow', '↑ uparrow', '↕ updownarrow', '⇓ Downarrow', '⇑ Uparrow', '⇕ Updownarrow', '↪ hookrightarrow', '↣ rightarrowtail',
    '↠ twoheadrightarrow', '↦ mapsto', '↤ mapsfrom', '← leftarrow', '↔ leftrightarrow', '⇒ Rightarrow', '⇐ Leftarrow', '⇔ Leftrightarrow']), 70)
_prefixop('log', '\\log', 70)
_prefix('±', '\\pm', 70)
_infixchain('\\,', '\\,', 72)
_infixr('^', '^', 75)
_infixr('_', '_', 77)
_aroundfix([('|','|','|','|'), ('⌊','⌋','\\lfloor ','\\rfloor '), ('⌈','⌉','\\lceil ','\\rceil')], 80)
_aroundfix([('⟨','⟩','\\langle','\\rangle'), ('⟦','⟧','\\llbracket','\\rrbracket')], 100)
_postfix("'", "'", 100)
_infix('|', '|', 37, 'pipe')
_infix('⁄', '\\frac', 60, 'fracslash')
_prefix('\\{', '\\{', 38, 'setb')
_prefix('-', '-', 70, 'minus')
_prefix('√', '\\sqrt', 100, 'sqrt')
_prefix('[', '[', 100, 'bracket')
_prefix([('■','■'), ('█','█')], 100, 'matrix')
_prefix([('frac','\\frac'), ('root','\\root'), ('stackrel','\\stackrel')], 100, 'binary')

END = Node(')end)', tex='', bp=-1)
_LIT = Sym('(literal)', '')
_infx = re.compile(r"['^:,+⋅/)]")

TOKENIZERS = {'unicodemath': tokenize}

class Parser:
    def __init__(self, src, dialect='unicodemath'):
        self.dialect = dialect
        self.toks,self.i,self.token = TOKENIZERS[dialect](src),0,None
        self.advance()

    def advance(self, expected=None):
        if expected and self.token.sym != expected: raise ParseError(f"Expected '{expected}', got '{self.token.sym}'")
        if self.i >= len(self.toks):
            self.token = END
            return
        typ,sym = self.toks[self.i]
        self.i += 1
        if typ == 'number':
            self.token = Node(sym, tex='', typ='term', entry=_LIT)
            return
        if typ == 'function':
            e = Sym(sym, '\\text{'+sym+'}', 0, 'function')
            e.nudk = 'const'
        else: e = SYMS.get(sym) or _auto(sym)
        self.token = Node(sym, tex=e.tex, bp=e.lbp, typ=e.typ, entry=e)

    def expression(self, rbp, nbl=False):
        t = self.token
        self.advance()
        left = self.nud(t)
        while rbp < self.token.bp or (self.token.bp == 0 and not nbl and rbp < 72):
            if self.token.bp == 0 and not nbl and rbp < 72:
                e = SYMS['\\,']
                newleft = self._l_chain(Node('\\,', tex=e.tex, bp=72, typ='term', entry=e), left, True)
                if left.sym == '\\,': left.arg.append(newleft.arg[1])
                else: left = newleft
            if rbp < self.token.bp:
                t = self.token
                self.advance()
                left = self.led(t, left, nbl)
        return left

    def nud(self, t): return getattr(self, '_n_'+t.entry.nudk)(t) if t.entry and t.entry.nudk else t
    def led(self, t, left, nbl): return getattr(self, '_l_'+t.entry.ledk)(t, left, nbl)

    def _n_const(self, t):
        if t.typ == 'function' and not _infx.match(self.token.sym[0]): t.arg,t.bp,t.kind = self.expression(100),100,'funcapp'
        return t

    def _n_paren(self, t):
        e = self.expression(0)
        self.advance(t.entry.closer)
        return e

    def _n_prefix(self, t):
        if not _infx.match(self.token.sym[0]): t.arg,t.bp,t.kind = self.expression(t.entry.nbp),t.entry.nbp,'prefix'
        return t

    def _n_minus(self, t):
        if self.token.sym == '}': return t
        try: t.arg = self.expression(70)
        except ParseError: return t
        t.bp,t.kind = 70,'minus'
        return t

    def _n_prefixop(self, t):
        if self.token.sym == '_':
            self.advance('_')
            t.arg = self.expression(75, True)
        if self.token.sym == '^':
            self.advance('^')
            t.arg2 = self.expression(t.entry.nbp, True)
        t.arg3,t.bp,t.kind = self.expression(t.entry.nbp),t.entry.nbp,'prefixop'
        return t

    def _n_around(self, t):
        t.arg = self.expression(45)
        self.advance(t.entry.closer)
        t.bp,t.kind = t.entry.nbp,'around'
        return t

    def _n_quant(self, t):
        t.arg,t.arg2,t.bp,t.kind = self.expression(35, True),self.expression(35),35,'quant'
        return t

    def _n_setb(self, t):
        a = []
        if self.token.sym != '\\}':
            a.append(self.expression(38, True))
            if self.token.sym in ('|', ':', '∣'):
                self.advance()
                t.arg,t.arg2 = a[0],self.expression(10)
            elif self.token.sym == ',':
                self.advance(',')
                while True:
                    a.append(self.expression(0))
                    if self.token.sym != ',': break
                    self.advance(',')
                t.arg = a
            else: t.arg = a
        else: t.arg = a
        self.advance('\\}')
        t.typ,t.bp,t.kind = 'set',60,'setb'
        return t

    def _n_sqrt(self, t):
        if self.token.sym == '[':
            self.advance('[')
            t.arg2 = self.expression(40)
            self.advance(']')
        t.arg,t.bp,t.kind = self.expression(100),100,'sqrt'
        return t

    def _n_bracket(self, t):
        if self.dialect == 'asciimath': return self._n_amlist(t)
        t.arg = self.expression(45)
        self.advance(']')
        t.bp,t.kind = 80,'bracket'
        return t

    def _l_infix(self, t, left, nbl):
        t.arg,t.arg2,t.kind = left,self.expression(t.entry.ledbp, nbl),'infix'
        return t

    def _l_infixr(self, t, left, nbl):
        t.arg,t.arg2,t.kind = left,self.expression(t.entry.ledbp-1, nbl),'infixr'
        return t

    def _l_chain(self, t, left, nbl):
        a = [left]
        if self.token.sym != ')end)':
            while True:
                a.append(self.expression(t.entry.ledbp, nbl))
                if self.token.sym != t.sym: break
                self.advance(t.sym)
        t.arg,t.kind = a,'chain'
        return t

    def _l_postfix(self, t, left, nbl):
        t.arg,t.bp,t.kind = left,t.entry.ledbp,'postfix'
        return t

    def _l_pipe(self, t, left, nbl):
        t.arg,t.arg2 = left,self.expression(37, nbl)
        if self.token.sym == '|':
            self.advance()
            right = Node('|', tex='|', bp=80, arg=t.arg2, kind='absr')
            return Node('\\,', tex='\\,', bp=72, arg=[left, right], kind='abschain')
        t.kind = 'infix'
        return t

    def _n_amlist(self, t):
        a = [self.expression(45)]
        while self.token.sym == ',':
            self.advance(',')
            a.append(self.expression(45))
        self.advance(']')
        if len(a) > 1 and all(x.kind == 'amlist' for x in a) and len({len(x.arg) for x in a}) == 1:
            return Node('■', tex='bmatrix', bp=100, kind='matrix', arg=[Node('&', kind='mrow', arg=x.arg) for x in a])
        t.arg,t.bp,t.kind = a,80,'amlist'
        return t

    def _n_matrix(self, t):
        self.advance('(')
        rows,row = [],[]
        while True:
            row.append(self.expression(0))
            if self.token.sym == '&': self.advance()
            elif self.token.sym == '@':
                self.advance()
                rows.append(row)
                row = []
            else: break
        rows.append(row)
        self.advance(')')
        t.arg = [Node('&', kind='mrow', arg=r) for r in rows]
        t.tex = 'aligned' if t.sym == '█' else 'matrix'
        t.bp,t.kind = 100,'matrix'
        return t

    def _n_binary(self, t):
        t.arg,t.arg2,t.bp,t.kind = self.expression(100),self.expression(100),100,t.sym
        return t

    def _l_fracslash(self, t, left, nbl):
        t.arg,t.arg2,t.kind = left,self.expression(t.entry.ledbp, nbl),'frac'
        return t

def _auto(sym):
    s = Sym(sym)
    s.nudk = 'const'
    return s

def parse(
    src, # Linear-format math source, e.g. '∑_(i=1)^n i^2'
    dialect='unicodemath', # Source dialect: 'unicodemath' or 'asciimath'
):
    "Parse `src` into a `Node` tree for `to_latex` etc"
    if dialect not in TOKENIZERS: raise ValueError(f'Unknown dialect: {dialect}')
    return Parser(src, dialect).expression(0)

def prefixform(t):
    "Parse-tree check format: `sym(arg,arg2,...)`, constants bare"
    st = t.sym + '('
    if t.arg is not None: st += ','.join(prefixform(x) for x in t.arg) if isinstance(t.arg, list) else prefixform(t.arg)
    if t.arg2 is not None: st += ',' + prefixform(t.arg2)
    if t.arg3 is not None: st += ',' + prefixform(t.arg3)
    return st[:-1] if st[-1] == '(' else st + ')'
