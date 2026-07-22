"""AsciiMath dialect: a longest-match tokenizer aliasing AsciiMath names onto the shared symbol table.

Symbol facts follow the published syntax list at asciimath.org. Registering here adds
'asciimath' to `TOKENIZERS`, so `parse(src, dialect='asciimath')` works once this module loads."""

from .core import TOKENIZERS, _number

__all__ = []

_AM = {'*':'⋅', '**':'*', '//':'/', '/':'⁄', 'xx':'×', '-:':'÷', '@':'∘', 'o+':'⊕', 'o.':'⊙', 'ox':'⊗', 'sum':'∑', 'prod':'∏', '^^':'∧', '^^^':'⋀',
    'vv':'∨', 'vvv':'⋁', 'nn':'∩', 'nnn':'⋂', 'uu':'∪', 'uuu':'⋃', '+-':'±', 'setminus':'∖', '!=':'≠', '<=':'≤', '>=':'≥', '-<':'≺', '>-':'≻',
    'in':'∈', '!in':'∉', 'sub':'⊂', 'sup':'⊃', 'sube':'⊆', 'supe':'⊇', '-=':'≡', '~=':'≅', '~~':'≈', 'prop':'∝', 'not':'¬', '=>':'⟹', 'iff':'⟺',
    'AA':'∀', 'EE':'∃', '_|_':'⊥', 'TT':'⊤', '|--':'⊢', '|==':'⊨', 'oo':'∞', 'int':'∫', 'oint':'∮', 'del':'∂', 'grad':'∇', 'O/':'∅', 'aleph':'ℵ',
    '/_':'∠', 'cdots':'⋯', 'vdots':'⋮', 'ddots':'⋱', '...':'…', 'NN':'ℕ', 'ZZ':'ℤ', 'QQ':'ℚ', 'RR':'ℝ', 'CC':'ℂ', '->':'→', 'to':'→', '|->':'↦',
    'uarr':'↑', 'darr':'↓', 'larr':'←', 'harr':'↔', 'rarr':'→', 'rArr':'⇒', 'lArr':'⇐', 'hArr':'⇔', '(:':'⟨', ':)':'⟩', '|__':'⌊', '__|':'⌋',
    '|~':'⌈', '~|':'⌉', 'alpha':'α', 'beta':'β', 'gamma':'γ', 'Gamma':'Γ', 'delta':'δ', 'Delta':'Δ', 'epsilon':'ϵ', 'varepsilon':'ɛ', 'zeta':'ζ',
    'eta':'η', 'theta':'θ', 'vartheta':'ϑ', 'Theta':'Θ', 'iota':'ι', 'kappa':'κ', 'lambda':'λ', 'Lambda':'Λ', 'mu':'μ', 'nu':'ν', 'xi':'ξ',
    'Xi':'Ξ', 'pi':'π', 'Pi':'Π', 'rho':'ρ', 'sigma':'σ', 'Sigma':'Σ', 'tau':'τ', 'upsilon':'υ', 'phi':'ϕ', 'varphi':'φ', 'Phi':'Φ', 'chi':'χ',
    'psi':'ψ', 'Psi':'Ψ', 'omega':'ω', 'Omega':'Ω', 'sqrt':'√'}
_AM |= {k:k for k in 'and or frac root stackrel lim sin cos tan cot sec csc ln log det gcd lcm mod div'.split()}
_maxlen = max(map(len, _AM))

def am_tokenize(s):
    "Token `(typ, sym)` pairs with AsciiMath names mapped to shared-table symbols"
    toks,i,n = [],0,len(s)
    while i < n:
        c = s[i]
        if c <= ' ':
            i += 1
            continue
        if '0' <= c <= '9':
            i = _number(toks, s, i)
            continue
        for l in range(min(_maxlen, n-i), 0, -1):
            if s[i:i+l] in _AM:
                toks.append((None, _AM[s[i:i+l]]))
                i += l
                break
        else:
            toks.append((None, c))
            i += 1
    return toks

TOKENIZERS['asciimath'] = am_tokenize
