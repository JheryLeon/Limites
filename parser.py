import re


def insert_implicit_mul(s):
    """Inserta * donde hay multiplicación implícita.
    
    2x → 2*x, x(x+1) → x*(x+1), (x+1)(x-1) → (x+1)*(x-1)
    No afecta funciones: sin(x), ln(x), sqrt(x), etc.
    """
    s = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', s)
    s = re.sub(r'(?<![a-zA-Z])([a-zA-Z])\(', r'\1*(', s)
    s = re.sub(r'\)\s*\(', r')*(', s)
    s = re.sub(r'\)\s*([a-zA-Z])', r')*\1', s)
    s = re.sub(r'\)\s*(\d)', r')*\1', s)
    return s


def parse_limit_string(s):
    """Interpreta notación natural de límites.
    
    Ejemplos aceptados:
      lim x→0 sin(x)/x
      lim_{x→0} sin(x)/x
      lim x->0 sin(x)/x
      lím x→0 sen(x)/x
      lim x→∞ (2x²+1)/(x²-3)
      lim x→0+ x·ln(x)
      lim x→0⁻ x·ln(x)
      lim x→-1 (x³+1)/(x²-1)
      lim x→0⁺ x·ln(x)
      lím_{x→0⁺} x·ln(x)
    """
    s = s.strip()
    if not s:
        return None

    # Normalizar: reemplazar lím → lim, ⁺ → +, ⁻ → -, · → *, × → *
    s = s.replace('lím', 'lim').replace('Lím', 'Lim')
    s = s.replace('⁺', '+').replace('⁻', '-')
    s = s.replace('·', '*').replace('×', '*')

    # Quitar prefijo "lim" con o sin llaves
    m = re.match(r'lim(?:_\{)?\s*', s)
    if not m:
        return None
    s = s[m.end():]

    # Extraer variable (una letra, puede ir seguida de llave de cierre)
    m = re.match(r'([a-zA-Z])\s*\}?\s*', s)
    if not m:
        return None
    var = m.group(1)
    s = s[m.end():]

    # Flecha: → o -> o to
    m = re.match(r'(?:→|->|to)\s*', s)
    if not m:
        return None
    s = s[m.end():]

    # Extraer punto: puede ser número, ∞, -∞, +∞, pi, π, e
    m = re.match(r'([+-]?(?:\d+(?:\.\d+)?|∞|oo|inf|pi|π|e))', s)
    if not m:
        return None
    point = m.group(1)
    s = s[m.end():]

    # Dirección: +, -, ⁺, ⁻ (puede venir después del número o como superíndice)
    direction = ''
    if s.startswith('+') or s.startswith('⁺'):
        direction = '+'
        s = s[1:]
    elif s.startswith('-') or s.startswith('⁻'):
        direction = '-'
        s = s[1:]

    # Cerrar llave pendiente (de lim_{...})
    if s.startswith('}'):
        s = s[1:]

    # El resto es la expresión
    expr = s.strip()

    if not expr:
        return None

    expr = insert_implicit_mul(expr)

    return {
        'variable': var,
        'point': point,
        'direction': direction,
        'expression': expr,
    }


def build_limit_latex(parsed, expr_tex):
    """Construye el LaTeX completo del límite a partir del parseo."""
    var = parsed['variable']
    pt = parsed['point']

    # Normalizar punto a LaTeX
    pt_tex = pt
    if pt in ('∞', 'oo', 'inf', '+∞', '+oo', '+inf'):
        pt_tex = '\\infty'
    elif pt in ('-∞', '-oo', '-inf'):
        pt_tex = '-\\infty'
    elif pt == 'π':
        pt_tex = '\\pi'
    elif pt == 'pi':
        pt_tex = '\\pi'
    elif pt == 'e':
        pt_tex = 'e'

    dir_str = ''
    if parsed['direction'] == '+':
        dir_str = '^{+}'
    elif parsed['direction'] == '-':
        dir_str = '^{-}'

    return f'\\lim_{{{var} \\to {pt_tex}{dir_str}}} {expr_tex}'
