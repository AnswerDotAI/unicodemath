import json
from pathlib import Path
from fastcore.test import test_eq as teq
from unicodemath import parse, to_latex, prefixform

fixtures = Path(__file__).parent/'fixtures'

def chk(samples, dialect='unicodemath'):
    for src, (latex, pform) in samples.items():
        t = parse(src, dialect=dialect)
        teq((to_latex(t), prefixform(t), src), (latex, pform, src))

am_samples = {  # chkstyle: ignore-node
    'a/b': (r'\frac{a}{b}', '⁄(a,b)'),
    '(a+b)/(c-d)': (r'\frac{a+b}{c-d}', '⁄(+(a,b),-(c,d))'),
    'frac(a)(b+1)': (r'\frac{a}{b+1}', 'frac(a,+(b,1))'),
    'root(3)(x+1)': (r'\sqrt[3]{x+1}', 'root(3,+(x,1))'),
    'x^2+y^2=r^2': ('x^2+y^2 = r^2', '=(+(^(x,2),^(y,2)),^(r,2))'),
    'AA x in RR x^2>=0': (r'\forall x \in \mathbb R (x^2 \ge 0)', '∀(∈(x,ℝ),≥(^(x,2),0))'),
    'sum_(k=1)^n k': (r'\sum_{k = 1}^nk', '∑(=(k,1),n,k)'),
    'int_0^oo e^(-x) dx': (r'\int_0^\infty e^{-x}dx', r'∫(0,∞,\,(^(e,-(x)),d,x))'),
    'a-:b': (r'a\div b', '÷(a,b)'),
    '(x+1)(x-1)': (r'(x+1)(x-1)', r'\,(+(x,1),-(x,1))'),
    'stackrel(def)(=)': (r'\stackrel{def}{=}', r'stackrel(\,(d,e,f),=)'),
    '[[a,b],[c,d]]': (r'\begin{bmatrix}a&b\\c&d\end{bmatrix}', '■(&(a,b),&(c,d))'),
}

um_samples = {  # chkstyle: ignore-node
    '■(a&b@c&d)': (r'\begin{matrix}a&b\\c&d\end{matrix}', '■(&(a,b),&(c,d))'),
    '█(x&=y@z&=w)': (r'\begin{aligned}x&=y\\z&=w\end{aligned}', r'█(&(x,\,(=,y)),&(z,\,(=,w)))'),
    'A = ■(a&b@c&d)': (r'A = \begin{matrix}a&b\\c&d\end{matrix}', '=(A,■(&(a,b),&(c,d)))'),
}

def test_jipsen_samples(): chk(json.loads((fixtures/'jipsen_samples.json').read_text()))
def test_asciimath(): chk(am_samples, 'asciimath')
def test_matrices(): chk(um_samples)
