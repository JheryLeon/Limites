import re
import sympy as sp
from sympy import (
    symbols, Symbol, limit, oo, nan, pi, E, zoo,
    simplify, factor, expand, diff, latex, sympify,
    sqrt, Rational, conjugate, together, apart,
    Pow, Mul, Add, Function, fraction, cancel,
    trigsimp, expand_trig, nsimplify, degree,
    log, ln, exp, sin, cos, tan, cot, sec, csc,
    sign, Abs, Wild
)


def _normalize_expression(expr_str):
    expr = expr_str.strip().replace(' ', '')
    expr = expr.replace('âˆš', 'sqrt').replace('V(', 'sqrt(').replace('v(', 'sqrt(')
    expr = expr.replace('Ï€', 'pi').replace('âˆž', 'oo')
    expr = expr.replace('Ã—', '*').replace('Â·', '*')
    expr = expr.replace('Â²', '^2').replace('Â³', '^3').replace('â´', '^4')
    expr = expr.replace('âº', '+').replace('â»', '-')
    expr = expr.replace('âˆ’', '-')
    expr = expr.replace('[', '(').replace(']', ')')
    expr = expr.replace('{', '(').replace('}', ')')
    expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)
    expr = re.sub(r'\\sqrt\{([^{}]+)\}', r'sqrt(\1)', expr)
    return expr


def expr_to_latex(expr):
    if expr == oo:
        return '\\infty'
    if expr == -oo:
        return '-\\infty'
    if expr == zoo:
        return '\\infty'
    if expr == pi:
        return '\\pi'
    if expr == E:
        return 'e'
    if isinstance(expr, sp.Add):
        pos_terms = []
        neg_terms = []
        for arg in expr.args:
            if arg.is_Mul and arg.args[0].is_Number and arg.args[0] < 0:
                abs_arg = sp.Mul(-arg.args[0], *arg.args[1:]) if len(arg.args) > 2 else -arg
                neg_terms.append(expr_to_latex(abs_arg))
            elif arg.is_Number and arg < 0:
                neg_terms.append(expr_to_latex(-arg))
            else:
                pos_terms.append(expr_to_latex(arg))
        parts = []
        first = True
        for tex in pos_terms:
            if first:
                parts.append(tex)
                first = False
            else:
                parts.append(f'+ {tex}')
        for tex in neg_terms:
            if first:
                parts.append(f'-{tex}')
                first = False
            else:
                parts.append(f'- {tex}')
        return ' '.join(parts)
    if isinstance(expr, sp.Mul):
        coeff = 1
        den_coeff = 1
        num_rest = []
        den_rest = []
        for arg in expr.args:
            if arg.is_Integer:
                coeff *= arg
            elif arg.is_Rational:
                coeff *= arg.p
                den_coeff *= arg.q
            elif arg.is_Pow and arg.exp == -1 and arg.base.is_Integer:
                den_coeff *= arg.base
            elif arg.is_Pow and arg.exp == -1:
                den_rest.append(arg.base)
            elif arg.is_Pow and isinstance(arg.exp, sp.Number) and arg.exp < 0:
                den_rest.append(sp.Pow(arg.base, -arg.exp))
            else:
                num_rest.append(arg)

        if den_rest:
            num = sp.Mul(coeff, *num_rest) if coeff != 1 or num_rest else sp.Integer(1)
            den = sp.Mul(den_coeff, *den_rest) if den_coeff != 1 or den_rest else sp.Integer(1)
            return f'\\frac{{{expr_to_latex(num)}}}{{{expr_to_latex(den)}}}'

        if den_coeff != 1:
            rest = sp.Mul(*num_rest) if num_rest else sp.Integer(1)
            frac = f'\\frac{{{coeff}}}{{{den_coeff}}}'
            if rest != 1:
                return f'{frac} \\, {expr_to_latex(rest)}'
            return frac

        if num_rest:
            return latex(expr)
    if isinstance(expr, sp.Pow):
        base, exp = expr.args
        # Square root: x^{1/2} -> \sqrt{x}
        if exp == sp.Rational(1, 2):
            base_tex = expr_to_latex(base)
            if isinstance(base, (sp.Add, sp.Mul)):
                base_tex = f'\\left({base_tex}\\right)'
            return f'\\sqrt{{{base_tex}}}'
        # Nth root: x^{1/n} -> \sqrt[n]{x}
        if isinstance(exp, sp.Rational) and exp.p == 1 and exp.q > 2:
            base_tex = expr_to_latex(base)
            if isinstance(base, (sp.Add, sp.Mul)):
                base_tex = f'\\left({base_tex}\\right)'
            return f'\\sqrt[{exp.q}]{{{base_tex}}}'
        # Negative exponent: x^{-n} -> \frac{1}{x^{n}}
        if exp.is_Number and exp < 0:
            pos_exp = -exp
            base_tex = expr_to_latex(base)
            if isinstance(base, sp.Add):
                base_tex = f'\\left({base_tex}\\right)'
            if pos_exp == 1:
                return f'\\frac{{1}}{{{base_tex}}}'
            exp_tex = expr_to_latex(pos_exp)
            return f'\\frac{{1}}{{{base_tex}^{{{exp_tex}}}}}'
        base_tex = expr_to_latex(base)
        if exp.is_Mul:
            exp_clean = sp.together(exp)
        elif exp.is_Pow and exp.exp == -1:
            exp_clean = sp.together(exp)
        else:
            exp_clean = exp
        exp_tex = expr_to_latex(exp_clean)
        if isinstance(base, sp.Add):
            return f'\\left({base_tex}\\right)^{{{exp_tex}}}'
        return f'{base_tex}^{{{exp_tex}}}'
    return latex(expr)


class LimitSolver:
    FORM_NAMES = {
        '0/0': '0/0',
        'âˆž/âˆž': '\\infty/\\infty',
        '0Â·âˆž': '0 \\cdot \\infty',
        'âˆž-âˆž': '\\infty - \\infty',
        '0^0': '0^{0}',
        'âˆž^0': '\\infty^{0}',
        '1^âˆž': '1^{\\infty}',
    }

    def __init__(self, expr_str, var_str='x', point_str='0', direction=None):
        self.var = Symbol(var_str, real=True)
        self.expr_str = expr_str
        self.expr = self._parse_expr(expr_str)
        self.point = self._parse_point(point_str)
        self.direction = direction
        self.steps = []
        self._limit_type = None

    def _parse_expr(self, s):
        try:
            if '\\' in s:
                from sympy.parsing.latex import parse_latex
                try:
                    try:
                        expr = parse_latex(s, implicit_multiplication=True)
                    except TypeError:
                        expr = parse_latex(s)
                    # Substitute symbols with matching names to self.var
                    var_map = {}
                    for sym in expr.free_symbols:
                        if sym.name == self.var.name:
                            var_map[sym] = self.var
                    if var_map:
                        expr = expr.subs(var_map)
                    # Normalize symbol 'e' to Euler's number
                    from sympy.core.numbers import Exp1
                    if sp.Symbol('e') in expr.free_symbols:
                        expr = expr.subs(sp.Symbol('e'), sp.E)
                    # Normalize FiniteSet to its element (parse_latex can produce {x} as set)
                    from sympy.sets.sets import FiniteSet
                    def _unwrap_finiteset(e):
                        if isinstance(e, FiniteSet) and len(e.args) == 1:
                            return e.args[0]
                        return e
                    if any(isinstance(e, FiniteSet) for e in sp.preorder_traversal(expr)):
                        expr = expr.replace(lambda e: isinstance(e, FiniteSet) and len(e.args) == 1,
                                            lambda e: e.args[0])
                    # Fix implicit multiplication: f(expr) -> f*expr when f matches variable
                    var_name = self.var.name
                    from sympy.core.function import AppliedUndef
                    def _is_func_call(e):
                        return isinstance(e, AppliedUndef) and str(e.func) == var_name
                    def _replace_func(e):
                        return sp.Mul(sp.Symbol(var_name), e.args[0])
                    if any(_is_func_call(e) for e in sp.preorder_traversal(expr)):
                        expr = expr.replace(_is_func_call, _replace_func)
                    return expr
                except Exception:
                    if re.search(r'\\(frac|sqrt|sin|cos|tan|log|ln|left|right)', s):
                        raise ValueError(
                            "No se pudo interpretar la expresión LaTeX. "
                            "Verifica que la expresión esté bien formada."
                        )
                    pass

            s = _normalize_expression(s)
            s = s.replace('^', '**')
            s = s.replace('[', '(').replace(']', ')')
            local_dict = {
                self.var.name: self.var,
                'e': sp.E,
                'ln': sp.log,
                'log': sp.log,
                'sen': sp.sin,
                'sin': sp.sin,
                'cos': sp.cos,
                'tan': sp.tan,
                'tg': sp.tan,
                'cot': sp.cot,
                'cotg': sp.cot,
                'sec': sp.sec,
                'csc': sp.csc,
                'arcsen': sp.asin,
                'arccos': sp.acos,
                'arctg': sp.atan,
                'sqrt': sp.sqrt,
                'exp': sp.exp,
            }
            expr = sympify(s, locals=local_dict, evaluate=False)
            return expr
        except Exception as e:
            raise ValueError(f"Error al parsear la expresiÃ³n: {e}")

    def _parse_point(self, s):
        s = s.strip().lower().replace(' ', '')
        mapping = {
            'oo': oo, 'inf': oo, 'âˆž': oo, 'infinito': oo, '+oo': oo, '+inf': oo, '+âˆž': oo,
            '-oo': -oo, '-inf': -oo, '-âˆž': -oo, '-infinito': -oo,
            'pi': pi, 'Ï€': pi,
            'e': E,
        }
        if s in mapping:
            return mapping[s]
        try:
            return Rational(s)
        except:
            try:
                return sympify(s)
            except:
                raise ValueError(f"No se pudo interpretar el punto: {s}")

    def _latex(self, expr):
        return expr_to_latex(expr)

    def _point_tex(self):
        if self.point == oo:
            return '\\infty'
        if self.point == -oo:
            return '-\\infty'
        if self.point == pi:
            return '\\pi'
        if self.point == E:
            return 'e'
        return self._latex(self.point)

    def _substitute_point_tex(self, expr):
        point_token = 'oo'
        if self.point == -oo:
            point_token = '-oo'
        elif self.point == pi:
            point_token = 'pi'
        elif self.point == E:
            point_token = 'e'
        else:
            point_token = str(self.point)

        expr_text = str(expr).replace(self.var.name, point_token)
        try:
            substituted = sympify(expr_text, locals={self.var.name: self.var}, evaluate=False)
            return self._latex(substituted)
        except Exception:
            try:
                return self._latex(expr.subs(self.var, self.point))
            except Exception:
                return self._latex(expr)

    def _limit_tex(self, expr):
        pt = self._point_tex()
        if self.direction == '+':
            arrow = f'\\to {pt}^{{\\+}}'
        elif self.direction == '-':
            arrow = f'\\to {pt}^{{-}}'
        else:
            arrow = f'\\to {pt}'
        expr_tex = self._latex(expr)
        if isinstance(expr, sp.Add):
            expr_tex = f'\\left({expr_tex}\\right)'
        return f'\\lim_{{{self.var.name} {arrow}}} {expr_tex}'

    def _substitution_tex(self, expr):
        """Generate LaTeX showing expr with variable replaced by the point value.
        Returns None if the point is infinite (substitution not meaningful)."""
        if self.point in (oo, -oo, zoo):
            return None
        pt = self._point_tex()
        var = self.var.name
        latex_str = self._latex(expr)
        wrapped = '(' + pt + ')' if pt not in ('\\infty', '-\\infty') else pt
        import re
        sub_latex = re.sub(
            r'(?<![a-zA-Z\\])' + re.escape(var) + r'(?![a-zA-Z])',
            wrapped,
            latex_str
        )
        if sub_latex == latex_str:
            return None
        return sub_latex

    def _paso1_indet_tex(self, expr, form_tex):
        """Build paso 1 tex showing the limit, substitution, and indeterminate form."""
        limit_tex = self._limit_tex(expr)
        sub_tex = self._substitution_tex(expr)
        if sub_tex:
            return f'{limit_tex} = {sub_tex} \\text{{ es una indeterminaciÃ³n }} \\boxed{{{form_tex}}}'
        return f'{limit_tex} \\text{{ es una indeterminaciÃ³n }} \\boxed{{{form_tex}}}'

    def _add_step(self, title, tex='', description='', step_type='info'):
        self.steps.append({
            'title': title,
            'tex': tex,
            'description': description,
            'type': step_type,
        })

    def _safe_sub(self, expr, point=None):
        if point is None:
            point = self.point
        try:
            if point in (oo, -oo):
                from sympy import degree as sp_degree
                try:
                    deg = sp_degree(expr, self.var)
                    if deg > 0:
                        coeff = sp.expand(expr).coeff(self.var**deg)
                        if coeff > 0:
                            return oo if point == oo else (-oo if point == -oo else oo)
                        elif coeff < 0:
                            return -oo if point == oo else (oo if point == -oo else -oo)
                except:
                    pass
                try:
                    lim = sp.limit(expr, self.var, point)
                    if lim in (oo, -oo):
                        return lim
                    if lim in (nan, zoo):
                        return lim
                    return lim
                except:
                    pass
            expr_str = str(expr)
            clean = sympify(expr_str, locals={self.var.name: self.var})
            val = clean.subs(self.var, point)
            val = nsimplify(val)
            reduced = sp.together(val)
            if reduced in (nan, zoo, oo, -oo):
                return reduced
            return val
        except Exception:
            return nan

    def _is_zero(self, val):
        if val is None:
            return False
        if val == 0:
            return True
        if isinstance(val, sp.Float) and abs(val) < 1e-15:
            return True
        if val == 0.0:
            return True
        return False

    def _is_inf(self, val):
        if val is None:
            return False
        if val in (oo, -oo):
            return True
        if val == zoo:
            return True
        return False

    def _is_indeterminate(self, val):
        if val is None:
            return True
        if val == nan:
            return True
        if isinstance(val, sp.core.numbers.NaN):
            return True
        try:
            if val.is_NaN:
                return True
        except:
            pass
        return False

    def _contains_sqrt(self, expr):
        for sub in sp.preorder_traversal(expr):
            if isinstance(sub, sp.Pow) and sub.args[1] == Rational(1, 2):
                return True
            if isinstance(sub, sp.Pow) and isinstance(sub.args[1], Rational) and sub.args[1].q == 2:
                return True
        return False

    def _detect_factor_type(self, expr):
        if not isinstance(expr, sp.Add) or len(expr.args) != 2:
            return None

        a, b = expr.args

        def classify(t):
            neg = False
            inner = t
            if inner.is_Mul and len(inner.args) == 2 and inner.args[0] == -1:
                inner = inner.args[1]
                neg = True
            elif inner.is_Number and inner < 0:
                inner = -inner
                neg = True
            is_const = not inner.has(self.var)
            exp = 1
            if isinstance(inner, sp.Pow):
                exp = inner.args[1]
                inner = inner.args[0]
            return (inner, exp, neg, is_const)

        t1 = classify(a)
        t2 = classify(b)

        signs = [t1[2], t2[2]]
        opp = signs[0] != signs[1]
        same = signs[0] == signs[1]

        exps = [t1[1], t2[1]]
        consts = [t1[3], t2[3]]

        # Difference of squares
        if opp:
            if 2 in exps or (exps[0] == exps[1] == 2):
                return 'diferencia de cuadrados'
            # Check x^even - perfect_square (e.g. x^4 - 16)
            if consts[0] != consts[1]:
                var_exp = exps[0] if not consts[0] else exps[1]
                const_val = t1[0] if consts[0] else t2[0]
                if var_exp % 2 == 0 and const_val.is_Integer:
                    root = int(const_val ** 0.5)
                    if root * root == const_val:
                        return 'diferencia de cuadrados'

        # Difference of cubes
        if opp and (3 in exps):
            return 'diferencia de cubos'

        # Sum of cubes
        if same and (3 in exps):
            return 'suma de cubos'

        return None

    def _classify_expr(self, expr):
        has_trig = False
        has_log = False
        has_e = False
        has_exp = False
        has_radical = False

        for sub in sp.preorder_traversal(expr):
            if isinstance(sub, sp.Pow) and isinstance(sub.args[1], sp.Rational) and sub.args[1].q == 2:
                has_radical = True
            if isinstance(sub, sp.Pow) and sub.args[1].has(self.var):
                has_exp = True
            if sub == sp.E:
                has_e = True
            fn = getattr(sub, 'func', None)
            if fn:
                if fn in (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc):
                    has_trig = True
                if fn in (sp.log, sp.ln):
                    has_log = True
                if fn == sp.exp:
                    has_e = True

        if has_e:
            return 'logarÃ­tmico'
        if has_log:
            return 'logarÃ­tmico'
        if has_trig:
            return 'trigonomÃ©trico'
        if has_exp:
            return 'exponencial'
        if has_radical:
            return 'algebraico irracional'

        try:
            num, den = sp.fraction(sp.together(expr))
            if num.is_polynomial(self.var) and den.is_polynomial(self.var):
                return 'algebraico racional'
        except:
            pass

        return 'algebraico'

    def _rationalizing_conjugate(self, expr):
        if expr.func == Add:
            sqrt_parts = []
            non_sqrt_parts = []
            for term in expr.args:
                if self._contains_sqrt(term):
                    sqrt_parts.append(term)
                else:
                    non_sqrt_parts.append(term)
            if sqrt_parts:
                if non_sqrt_parts:
                    conj_parts = non_sqrt_parts + [-p for p in sqrt_parts]
                else:
                    conj_parts = [sqrt_parts[0]] + [-p for p in sqrt_parts[1:]]
                return sp.simplify(sp.Add(*conj_parts))
        if expr.func == Mul and len(expr.args) == 2:
            const, sqrt_term = None, None
            for arg in expr.args:
                if self._contains_sqrt(arg):
                    sqrt_term = arg
                else:
                    const = arg
            if const is not None and sqrt_term is not None:
                conj = sp.simplify(const - sqrt_term)
                return conj
        return None

    def _detect_form(self, expr=None):
        if expr is None:
            expr = self.expr
        point = self.point

        # Check Add forms first (based on original structure, not combined)
        if expr.func == Add:
            signs = []
            for arg in expr.args:
                v = self._safe_sub(arg)
                if v == oo:
                    signs.append('+')
                elif v == -oo:
                    signs.append('-')
                elif v == zoo:
                    signs.append('?')
            if len(signs) >= 2:
                has_plus = '+' in signs
                has_minus = '-' in signs
                has_q = '?' in signs
                if (has_plus and has_minus) or (has_q and (has_plus or has_minus)) or (signs.count('?') >= 2):
                    return 'âˆž-âˆž'
            return None

        num, den = expr.as_numer_denom()
        num_val = self._safe_sub(num)
        den_val = self._safe_sub(den)
        num_zero = self._is_zero(num_val)
        den_zero = self._is_zero(den_val)
        num_inf = self._is_inf(num_val)
        den_inf = self._is_inf(den_val)

        if num_zero and den_zero:
            return '0/0'
        if num_inf and den_inf:
            return 'âˆž/âˆž'

        if expr.func == Pow:
            base, exp = expr.args
            base_val = self._safe_sub(base)
            exp_val = self._safe_sub(exp)
            if self._is_zero(base_val) and self._is_zero(exp_val):
                return '0^0'
            if self._is_inf(base_val) and self._is_zero(exp_val):
                return 'âˆž^0'
            if base_val == 1 and self._is_inf(exp_val):
                return '1^âˆž'

        if expr.func == Mul:
            args_zero = any(self._is_zero(self._safe_sub(a)) for a in expr.args)
            args_inf = any(self._is_inf(self._safe_sub(a)) for a in expr.args)
            if args_zero and args_inf:
                return '0Â·âˆž'

        if self._is_indeterminate(num_val) or self._is_indeterminate(den_val):
            return None
        return None

    def solve(self):
        try:
            self._limit_type = self._classify_expr(self.expr)
            form = self._detect_form()

            # 0^0, âˆž^0, 1^âˆž are indeterminate but SymPy may evaluate them directly
            force_indeterminate = False
            if self.expr.func == Pow:
                b, e = self.expr.args
                bv = self._safe_sub(b)
                ev = self._safe_sub(e)
                if self._is_zero(bv) and self._is_zero(ev):
                    force_indeterminate = True
                if self._is_inf(bv) and self._is_zero(ev):
                    force_indeterminate = True
                if bv == 1 and self._is_inf(ev):
                    force_indeterminate = True

            if force_indeterminate:
                direct_val = nan
            else:
                direct_val = self._safe_sub(self.expr)

            if not self._is_indeterminate(direct_val):
                self._add_step(
                    'SustituciÃ³n directa',
                    f'{self._limit_tex(self.expr)} = {self._latex(direct_val)}',
                    f'Al sustituir {self.var.name} = {self._point_tex()} obtenemos el resultado directamente.',
                    'success'
                )
                return {
                    'steps': self.steps,
                    'result_tex': self._latex(direct_val),
                    'form': None,
                    'limit_type': None,
                    'error': None,
                }

            result = None
            if form in ('0/0', 'âˆž/âˆž', 'âˆž-âˆž', '1^âˆž', '0^0', 'âˆž^0'):
                if form == '0/0':
                    result = self._solve_0_over_0_detailed()
                elif form == 'âˆž/âˆž':
                    result = self._solve_inf_over_inf_detailed()
                elif form == 'âˆž-âˆž':
                    result = self._solve_inf_minus_inf_detailed()
                else:
                    result = self._solve_exponential_detailed(form)
                if result is not None and not self._is_indeterminate(result):
                    return {
                        'steps': self.steps,
                        'result_tex': self._latex(result),
                        'form': form,
                        'limit_type': self._limit_type,
                        'error': None,
                    }
                return self._solve_fallback()
            else:
                self._add_step(
                    'ExpresiÃ³n original',
                    f'{self._limit_tex(self.expr)}',
                    f'Vamos a calcular el lÃ­mite indicado.',
                    'expression'
                )
                form_tex = self.FORM_NAMES.get(form, form or 'desconocida')
                if form:
                    self._add_step(
                        'IndeterminaciÃ³n detectada',
                        f'{self._limit_tex(self.expr)} \\text{{ es una indeterminaciÃ³n }} \\boxed{{{form_tex}}}',
                        f'Al sustituir directamente obtenemos {form}. Aplicaremos tÃ©cnicas para resolverla.',
                        'warning'
                    )
                else:
                    self._add_step(
                        'Forma indeterminada',
                        f'\\text{{La expresiÃ³n presenta una indeterminaciÃ³n}}',
                        'La expresiÃ³n es indeterminada. Usaremos tÃ©cnicas generales.',
                        'warning'
                    )
                if form == '0/0':
                    result = self._solve_0_over_0()
                elif form == 'âˆž/âˆž':
                    result = self._solve_inf_over_inf()
                elif form == '0Â·âˆž':
                    result = self._solve_0_times_inf()
                elif form == 'âˆž-âˆž':
                    result = self._solve_inf_minus_inf()
                elif form in ('1^âˆž', '0^0', 'âˆž^0'):
                    result = self._solve_exponential(form)
                else:
                    result = self._solve_fallback()

                if result is not None and not self._is_indeterminate(result):
                    self._add_step(
                        'Resultado final',
                        f'\\boxed{{{self._limit_tex(self.expr)} = {self._latex(result)}}}',
                        f'El lÃ­mite es {self._latex(result)}.',
                        'success'
                    )
                    return {
                        'steps': self.steps,
                        'result_tex': self._latex(result),
                        'form': form,
                        'limit_type': self._limit_type,
                        'error': None,
                    }

                return self._solve_fallback()

        except Exception as e:
            return {
                'steps': self.steps,
                'result_tex': None,
                'form': None,
                'limit_type': None,
                'error': str(e),
            }

    def _solve_fallback(self, expr=None):
        if expr is None:
            expr = self.expr
        try:
            if self.direction:
                result = limit(expr, self.var, self.point, dir=self.direction)
            else:
                result = limit(expr, self.var, self.point)
            self._add_step(
                'CÃ¡lculo simbÃ³lico (SymPy)',
                f'{self._latex(expr)} \\to {self._latex(result)}',
                'Utilizamos el motor de cÃ¡lculo simbÃ³lico para obtener el resultado.',
                'success'
            )
            return result
        except Exception as e:
            self._add_step(
                'Error',
                '',
                f'No se pudo calcular el lÃ­mite: {str(e)}',
                'error'
            )
            return None

    def _factor_with_info(self, num, den):
        x = self.var
        num_f = factor(num)
        den_f = factor(den)
        if num_f == num and den_f == den:
            return None
        info = {
            'num_original': num,
            'den_original': den,
            'num_factored': num_f,
            'den_factored': den_f,
            'num_changed': num_f != num,
            'den_changed': den_f != den,
            'num_type': self._detect_factor_type(num) if num_f != num else None,
            'den_type': self._detect_factor_type(den) if den_f != den else None,
        }
        simplified = cancel(num_f / den_f)
        val = self._safe_sub(simplified)
        if self._is_indeterminate(val):
            return None
        return (simplified, val, info)

    def _rationalize_with_info(self, num, den):
        target = None
        is_num = False
        if self._contains_sqrt(num):
            target = num
            is_num = True
        elif self._contains_sqrt(den):
            target = den
            is_num = False
        else:
            return None
        conj = self._rationalizing_conjugate(target)
        if conj is None or conj == target:
            return None
        if is_num:
            new_num = sp.expand(num * conj)
            new_den = den * conj
        else:
            new_num = sp.expand(num * conj)
            new_den = den * conj
        new_expr = sp.cancel(new_num / new_den)
        val = self._safe_sub(new_expr)
        if not self._is_indeterminate(val):
            return (new_expr, val, {'target': target, 'conj': conj, 'is_num': is_num, 'both': False})
        # If still indeterminate, the other component may also have sqrt (e.g., both num and den have radicals).
        # Try rationalizing the ORIGINAL other component on the current new_expr.
        other_target = den if is_num else num
        if self._contains_sqrt(other_target):
            conj2 = self._rationalizing_conjugate(other_target)
            if conj2 is not None and conj2 != other_target:
                cur_num, cur_den = new_expr.as_numer_denom()
                if is_num:
                    new_num2 = sp.expand(cur_num * conj2)
                    new_den2 = cur_den * conj2
                else:
                    new_num2 = sp.expand(cur_num * conj2)
                    new_den2 = cur_den * conj2
                new_expr2 = sp.cancel(new_num2 / new_den2)
                val2 = self._safe_sub(new_expr2)
                if not self._is_indeterminate(val2):
                    return (new_expr2, val2, {'target': target, 'conj': conj, 'conj2': conj2, 'is_num': is_num, 'both': True})
        return None

    def _solve_trigonometric_0_over_0(self, expr=None):
        if expr is None:
            expr = self.expr
        self.steps = []
        x, point = self.var, self.point

        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '0/0'),
            'Se sustituye la tendencia de x para hallar la indeterminaciÃ³n.',
            'warning'
        )

        num, den = expr.as_numer_denom()

        # Try cos-specific solver first (handles 1-cos, cos-1 with x or xÂ²)
        result = self._solve_trig_with_cos(num, den, expr)
        if result is not None:
            return result

        # Try generic solver (handles arbitrary expressions with sin/tan terms)
        result = self._solve_trig_complex_generic(num, den, expr)
        if result is not None:
            return result

        # Try simple pattern detector (sin(kx)/(cx), tan(kx)/(cx), (1-cos(kx))/(cx))
        result = self._do_trig_step_by_step(num, den, expr)
        if result is not None:
            return result

        # Fallback: solve silently and show result
        val = self._solve_silent(expr)
        if val is not None and not self._is_indeterminate(val):
            limit_tex = self._limit_tex(expr)
            self._add_step(
                'Paso 2',
                f'\\text{{Resolvemos aplicando lÃ­mites trigonomÃ©tricos:}} \\\\'
                f'{limit_tex} = {self._latex(val)} \\\\'
                f'\\boxed{{{limit_tex} = {self._latex(val)}}}',
                'Se aplican lÃ­mites trigonomÃ©tricos fundamentales.',
                'info'
            )
            return val

        return self._solve_fallback(expr)

    def _detect_trig_numerator(self, num, c):
        x = self.var

        # Pattern: sin(kx) or a*sin(kx)
        if isinstance(num, (sp.sin, sp.tan)):
            trig_func = num
            a = 1
        elif num.is_Mul:
            trig_func = None
            a = 1
            for arg in sp.Mul.make_args(num):
                if isinstance(arg, (sp.sin, sp.tan)):
                    trig_func = arg
                elif arg.is_Number:
                    a *= arg
                else:
                    trig_func = None
                    break
            if trig_func is None:
                # Pattern: a * (1 - cos(kx))
                if isinstance(num, sp.Mul):
                    coeff_part, rest = num.as_coeff_Mul()
                    if isinstance(rest, sp.Add) and len(rest.args) == 2:
                        has_one = False
                        cos_func = None
                        for t in rest.args:
                            if t == 1:
                                has_one = True
                            elif t.is_Mul and t.args[0] == -1 and isinstance(t.args[1], sp.cos):
                                cos_func = t.args[1]
                        if has_one and cos_func is not None:
                            arg_inner = cos_func.args[0]
                            c2, vp = arg_inner.as_coeff_Mul()
                            if vp == x or vp == -x:
                                if vp == -x:
                                    c2 = -c2
                                return {
                                    'trig_type': 'one_minus_cos', 'trig_cmd': '\\cos',
                                    'special_limit_tex': '\\lim_{u \\to 0} \\frac{1 - \\cos u}{u} = 0',
                                    'a': coeff_part, 'k': c2,
                                    'result_val': 0,
                                }
                return None
        elif isinstance(num, sp.Add) and len(num.args) == 2:
            # Pattern: 1 - cos(kx) or cos(kx) - 1
            has_one = False
            cos_func = None
            is_neg = False  # true for cos(kx) - 1 pattern
            for t in num.args:
                if t == 1:
                    has_one = True
                elif t == -1:
                    has_one = True
                    is_neg = True
                elif t.is_Mul and t.args[0] == -1 and isinstance(t.args[1], sp.cos):
                    cos_func = t.args[1]
                elif isinstance(t, sp.cos):
                    # cos(kx) - 1 pattern (cos without leading -1)
                    cos_func = t
                    is_neg = True
            if has_one and cos_func is not None:
                arg_inner = cos_func.args[0]
                c2, vp = arg_inner.as_coeff_Mul()
                if vp == x or vp == -x:
                    if vp == -x:
                        c2 = -c2
                    return {
                        'trig_type': 'one_minus_cos', 'trig_cmd': '\\cos',
                        'special_limit_tex': '\\lim_{u \\to 0} \\frac{1 - \\cos u}{u} = 0',
                        'a': -1 if is_neg else 1, 'k': c2,
                        'result_val': 0,
                    }
            return None
        else:
            return None

        # sin or tan pattern
        arg_inner = trig_func.args[0]
        coeff, var_part = arg_inner.as_coeff_Mul()
        if var_part != x and var_part != -x:
            return None
        if var_part == -x:
            coeff = -coeff
        k = coeff
        trig_type = 'sin' if isinstance(trig_func, sp.sin) else 'tan'
        result_val = a * k / c
        trig_cmd = '\\sin' if trig_type == 'sin' else '\\tan'
        special_tex = (
            '\\lim_{u \\to 0} \\frac{\\sin u}{u} = 1' if trig_type == 'sin'
            else '\\lim_{u \\to 0} \\frac{\\tan u}{u} = 1'
        )
        return {
            'trig_type': trig_type, 'trig_cmd': trig_cmd,
            'special_limit_tex': special_tex,
            'a': a, 'k': k, 'result_val': result_val,
        }

    def _find_trig_terms_in_expr(self, expr):
        x = self.var
        terms = []
        for sub in sp.preorder_traversal(expr):
            if isinstance(sub, (sp.sin, sp.tan)):
                arg = sub.args[0]
                coeff, var_part = arg.as_coeff_Mul()
                if var_part == x or var_part == -x:
                    if var_part == -x:
                        coeff = -coeff
                    terms.append({
                        'type': 'sin' if isinstance(sub, sp.sin) else 'tan',
                        'expr': sub,
                        'k': coeff,
                        'subtype': 'sin_tan',
                    })
            elif isinstance(sub, sp.cos):
                arg = sub.args[0]
                coeff, var_part = arg.as_coeff_Mul()
                if var_part == x or var_part == -x:
                    if var_part == -x:
                        coeff = -coeff
                    terms.append({
                        'type': 'cos',
                        'expr': sub,
                        'k': coeff,
                        'subtype': 'cos',
                    })
        return terms

    def _solve_trig_with_cos(self, num, den, expr):
        x = self.var
        num_cos = [t for t in self._find_trig_terms_in_expr(num) if t['subtype'] == 'cos']
        den_cos = [t for t in self._find_trig_terms_in_expr(den) if t['subtype'] == 'cos']
        if not num_cos and not den_cos:
            return None
        try:
            result_val = sp.limit(expr, x, self.point)
            if result_val in (sp.nan, sp.zoo, None):
                return None
            result_val = sp.nsimplify(result_val)
        except Exception:
            return None

        result_tex = self._latex(result_val)
        limit_tex = self._limit_tex(expr)
        num_tex = self._latex(num)
        den_tex = self._latex(den)

        lines = []
        special_limits_strs = []

        for t_list, side_expr, other_expr in [
            (num_cos, num, den),
            (den_cos, den, num),
        ]:
            for t in t_list:
                k = t['k']
                try:
                    other_over_x2 = sp.limit(other_expr / (k**2 * x**2), x, self.point)
                    is_x2 = other_over_x2 not in (0, sp.nan, sp.zoo, None) and getattr(other_over_x2, 'is_finite', False)
                except Exception:
                    is_x2 = False
                try:
                    other_over_x = sp.limit(other_expr / (k * x), x, self.point)
                    is_x = other_over_x not in (sp.nan, sp.zoo, None) and getattr(other_over_x, 'is_finite', False)
                except Exception:
                    is_x = False

                if is_x2:
                    sl = f'{{\\color{{green}}\\lim_{{u \\to 0}} \\frac{{1 - \\cos u}}{{u^{{2}}}} = \\frac{{1}}{{2}}}}'
                    special_limits_strs.append(sl)
                elif is_x:
                    sl = f'{{\\color{{green}}\\lim_{{u \\to 0}} \\frac{{1 - \\cos u}}{{u}} = 0}}'
                    special_limits_strs.append(sl)

        if not special_limits_strs:
            return None

        sl_tex = ',\\ '.join(special_limits_strs)
        lines.append(f'\\text{{Se usan lÃ­mites trigonomÃ©tricos especiales:}} \\\\{sl_tex}')
        lines.append(f'\\frac{{{num_tex}}}{{{den_tex}}}')

        # Show transformation for xÂ²/(cos(kx)-1) type
        if num.is_Pow:
            base, exp = num.as_base_exp()
            if base == x and exp == 2 and den_cos:
                k_val = den_cos[0]['k']
                kx_str = f'{self._latex(k_val)}{x}' if k_val != 1 else str(x)
                lines.append(
                    f'= -\\frac{{{x}^{{2}}}}{{1 - \\cos({kx_str})}}'
                    f' = -\\frac{{1}}{{\\frac{{1 - \\cos({kx_str})}}{{{x}^{{2}}}}}}'
                )
                lines.append(f'{limit_tex} = {result_tex}')
            else:
                lines.append(f'{limit_tex} = {result_tex}')
        else:
            lines.append(f'{limit_tex} = {result_tex}')

        paso2_tex = ' \\\\ '.join(lines)
        paso2_tex = paso2_tex + ' \\\\ ' + f'\\boxed{{{limit_tex} = {result_tex}}}'
        self._add_step('Paso 2', paso2_tex, 'Se aplican lÃ­mites trigonomÃ©tricos especiales con coseno.', 'info')
        return result_val

    def _solve_trig_complex_generic(self, num, den, expr):
        x = self.var
        num_trig = self._find_trig_terms_in_expr(num)
        den_trig = self._find_trig_terms_in_expr(den)
        if not num_trig and not den_trig:
            return None
        try:
            result_val = sp.limit(expr, x, self.point)
            if result_val in (sp.nan, sp.zoo, None):
                return None
            result_val = sp.nsimplify(result_val)
        except Exception:
            return None

        result_tex = self._latex(result_val)
        limit_tex = self._limit_tex(expr)
        num_tex = self._latex(num)
        den_tex = self._latex(den)

        desc_parts = []
        if num_trig:
            kx_strs = [f"{self._latex(t['k'])}{x}" for t in num_trig]
            desc_parts.append(f"{' y '.join(kx_strs)} en el numerador")
        if den_trig:
            kx_strs = [f"{self._latex(t['k'])}{x}" for t in den_trig]
            desc_parts.append(f"{' y '.join(kx_strs)} en el denominador")

        desc_text = "Se multiplica y divide por " + ", ".join(desc_parts) + ":"
        lines = [f"\\text{{{desc_text}}}"]
        lines.append(f"\\frac{{{num_tex}}}{{{den_tex}}}")

        # Build transformed representation using symbolic replacement
        # Use single-letter symbols (a, b, c...) to avoid LaTeX braces around names
        import re as _re
        symbol_names = 'abcdefghijklmnopqrstuvwxyz'
        trig_syms = []
        new_num = num
        for i, t in enumerate(num_trig):
            if i >= len(symbol_names):
                break
            sym = sp.Symbol(symbol_names[i])
            trig_syms.append((sym, t))
            new_num = new_num.subs(t['expr'], t['k'] * x * sym)
        offset = len(num_trig)
        new_den = den
        for i, t in enumerate(den_trig):
            if offset + i >= len(symbol_names):
                break
            sym = sp.Symbol(symbol_names[offset + i])
            trig_syms.append((sym, t))
            new_den = new_den.subs(t['expr'], t['k'] * x * sym)

        trans_num_tex = self._latex(new_num)
        trans_den_tex = self._latex(new_den)
        for sym, t in trig_syms:
            trig_cmd = '\\sin' if t['type'] == 'sin' else '\\tan'
            k_str = self._latex(t['k'])
            sym_name = str(sym)
            replacement_tex = f'\\frac{{{trig_cmd}({k_str}{x})}}{{{k_str}{x}}}'
            trans_num_tex = trans_num_tex.replace(sym_name, replacement_tex)
            trans_den_tex = trans_den_tex.replace(sym_name, replacement_tex)

        lines.append(f"\\frac{{{trans_num_tex}}}{{{trans_den_tex}}}")

        # Build the limit line with green special limits
        green_parts = []
        for trig_list, prefix in [(num_trig, 'numerador'), (den_trig, 'denominador')]:
            for t in trig_list:
                trig_cmd = '\\sin' if t['type'] == 'sin' else '\\tan'
                k_str = self._latex(t['k'])
                tex = f'{{\\color{{green}}\\lim_{{u \\to 0}} \\frac{{{trig_cmd} u}}{{u}} = 1}}'
                green_parts.append(tex)

        # Compute the intermediate result (without applying limits)
        limit_expr_num = sp.simplify(sp.limit(num / x, x, self.point)) if self.point in (0,) else None
        limit_expr_den = sp.simplify(sp.limit(den / x, x, self.point)) if self.point in (0,) else None

        # For the result line: show how the limit evaluates with green 1
        if num_trig and den_trig:
            n_coeffs = [t['k'] for t in num_trig]
            d_coeffs = [t['k'] for t in den_trig]
            # Try to get non-trig coefficients
            num_non_trig = sp.simplify(sp.limit((num - sum(t['expr'] * 0 for t in num_trig)) / x, x, self.point)) if self.point in (0,) else 0
            # Actually: num/x = (non_trig_part + trig_parts) / x
            # For 2x - sin(3x): num/x = 2 - sin(3x)/x
            # After limit: 2 - 3
            # Better to just compute: num/x, replace sin(kx)/x -> k, evaluate at x->0
            try:
                num_over_x = sp.simplify(num / x)
                den_over_x = sp.simplify(den / x)
                # Replace each sin(kx) -> k*x in num_over_x
                # So 2 - sin(3x)/x becomes 2 - 3
                num_result_expr = num_over_x
                den_result_expr = den_over_x
                for t in num_trig:
                    num_result_expr = num_result_expr.subs(t['expr'] / x, t['k'])
                for t in den_trig:
                    den_result_expr = den_result_expr.subs(t['expr'] / x, t['k'])
                num_res_val = sp.limit(num_result_expr, x, self.point)
                den_res_val = sp.limit(den_result_expr, x, self.point)

                num_res_tex = self._latex(num_result_expr)
                den_res_tex = self._latex(den_result_expr)

                if den_res_val not in (0, sp.nan, sp.zoo, None):
                    # Add green special limit formula
                    special_limits_strs = []
                    for t in (num_trig + den_trig):
                        trig_cmd = '\\sin' if t['type'] == 'sin' else '\\tan'
                        k_str = self._latex(t['k'])
                        special_limits_strs.append(
                            f'{{\\color{{green}}\\lim_{{u \\to 0}} \\frac{{{trig_cmd} u}}{{u}} = 1}}'
                        )
                    if special_limits_strs:
                        sl_tex = ',\\ '.join(special_limits_strs)
                        lines.append(f'\\text{{Aplicando lÃ­mites trigonomÃ©tricos: }} {sl_tex}')
                    lines.append(
                        f'{limit_tex} = \\frac{{{num_res_tex}}}{{{den_res_tex}}} \\\\'
                        f'= \\frac{{{self._latex(num_res_val)}}}{{{self._latex(den_res_val)}}} = {result_tex}'
                    )
                else:
                    lines.append(f'{limit_tex} = {result_tex}')
            except Exception:
                lines.append(f'{limit_tex} = {result_tex}')
        else:
            lines.append(f'{limit_tex} = {result_tex}')

        paso2_tex = ' \\\\ '.join(lines)
        paso2_tex = paso2_tex + ' \\\\ ' + f'\\boxed{{{limit_tex} = {result_tex}}}'
        self._add_step('Paso 2', paso2_tex, desc_text, 'info')
        return result_val

    def _do_trig_step_by_step(self, num, den, expr):
        x = self.var

        # --- Denominator analysis ---
        # We need to express den = x * c, where c is finite and non-zero at the limit point.
        # First try simple pattern: den = (numeric) * x
        den_factors = sp.Mul.make_args(den)
        c_val = 1
        found_x = False
        is_simple_den = True
        for factor in den_factors:
            if factor == x:
                found_x = True
            elif factor.is_Number:
                c_val *= factor
            else:
                is_simple_den = False
                break
        if found_x and is_simple_den:
            c = c_val  # numeric coefficient
            den_over_x_tex = None
        else:
            # General case: compute den/x at the limit point
            try:
                den_over_x = sp.simplify(den / x)
                # Use sp.limit because _safe_sub may return nan for 0/0 forms
                sub_val = sp.limit(den_over_x, x, self.point)
                if sub_val is None or sub_val == 0 or sub_val in (sp.oo, -sp.oo):
                    return None
                if not sub_val.is_Number or sub_val.is_Boolean:
                    return None
                c_val = sub_val
                c = sub_val
                den_over_x_tex = self._latex(den_over_x)
            except Exception:
                return None

        pattern = self._detect_trig_numerator(num, c)
        if pattern is None:
            return None

        a, k = pattern['a'], pattern['k']
        trig_cmd = pattern['trig_cmd']
        special_limit_tex = pattern['special_limit_tex']
        result_val = pattern['result_val']

        limit_tex = self._limit_tex(expr)
        result_tex = self._latex(result_val)
        k_tex = self._latex(k)
        den_tex = self._latex(den)

        # Use factored den display for complex denominators
        if den_over_x_tex is not None:
            display_den_tex = f'x \\cdot \\left({den_over_x_tex}\\right)'
            display_c_tex = den_over_x_tex
        else:
            display_den_tex = den_tex
            display_c_tex = self._latex(c)

        lines = []
        kx_str = f'{k_tex}{x}' if k != 1 else str(x)

        if k == 1 and a == 1 and c == 1:
            lines.append(
                f'{limit_tex} = '
                f'{{\\color{{green}}{special_limit_tex}}}'
                f' = {result_tex}'
            )
            desc = f'Se aplica el lÃ­mite trigonomÃ©trico especial {special_limit_tex}.'
        elif pattern['trig_type'] == 'one_minus_cos':
            kc_frac = f'\\frac{{{k_tex}}}{{{display_c_tex}}}'
            lines.append(f'\\text{{Se multiplica y divide por }}{k_tex}:')
            if a == 1:
                transform = (
                    f'\\frac{{1 - {trig_cmd}({kx_str})}}{{{display_den_tex}}}'
                    f' = {kc_frac}'
                    f' \\cdot \\frac{{1 - {trig_cmd}({kx_str})}}{{{kx_str}}}'
                )
            else:
                transform = (
                    f'\\frac{{{self._latex(a)} \\left(1 - {trig_cmd}({kx_str})\\right)}}{{{display_den_tex}}}'
                    f' = {self._latex(a)} \\cdot {kc_frac}'
                    f' \\cdot \\frac{{1 - {trig_cmd}({kx_str})}}{{{kx_str}}}'
                )
            lines.append(transform)

            eq = f'{self._latex(a)} \\cdot {kc_frac}' if a != 1 else kc_frac
            lines.append(
                f'{limit_tex} = {eq}'
                f' \\cdot {{\\color{{green}}{special_limit_tex}}}'
                f' = {result_tex}'
            )
            desc = f'Se multiplica y divide por {k_tex}.'
        else:
            kc_frac = f'\\frac{{{k_tex}}}{{{display_c_tex}}}'
            lines.append(f'\\text{{Se multiplica y divide por }}{k_tex}:')
            if a == 1:
                transform = (
                    f'\\frac{{{trig_cmd}({kx_str})}}{{{display_den_tex}}}'
                    f' = {kc_frac}'
                    f' \\cdot \\frac{{{trig_cmd}({kx_str})}}{{{kx_str}}}'
                )
            elif a == -1:
                transform = (
                    f'\\frac{{-{trig_cmd}({kx_str})}}{{{display_den_tex}}}'
                    f' = -{kc_frac}'
                    f' \\cdot \\frac{{{trig_cmd}({kx_str})}}{{{kx_str}}}'
                )
            else:
                transform = (
                    f'\\frac{{{self._latex(a)} \\, {trig_cmd}({kx_str})}}{{{display_den_tex}}}'
                    f' = {self._latex(a)} \\cdot {kc_frac}'
                    f' \\cdot \\frac{{{trig_cmd}({kx_str})}}{{{kx_str}}}'
                )
            lines.append(transform)

            eq = f'-{kc_frac}' if a == -1 else (
                f'{self._latex(a)} \\cdot {kc_frac}' if a != 1 else kc_frac
            )
            lines.append(
                f'{limit_tex} = {eq}'
                f' \\cdot {{\\color{{green}}{special_limit_tex}}}'
                f' = {result_tex}'
            )
            desc = f'Se multiplica y divide por {k_tex}.'

        paso2_tex = ' \\\\ '.join(lines)
        paso2_tex = paso2_tex + ' \\\\ ' + f'\\boxed{{{limit_tex} = {result_tex}}}'
        self._add_step('Paso 2', paso2_tex, desc, 'info')

        return result_val

    def _detect_log_numerator(self, num):
        """Detect pattern a * e^{kx} + constant in numerator.
        Returns dict with has_minus_one, k, a, or None."""
        x = self.var
        if not isinstance(num, sp.Add):
            return None

        e_term = None
        e_coeff = 1
        constant = None

        for arg in num.args:
            if arg.is_Number:
                constant = int(arg)
            elif arg.func == sp.exp:
                if e_term is not None:
                    return None
                e_term = ('exp', arg)
            elif isinstance(arg, sp.Mul):
                coeff, rest = arg.as_coeff_Mul()
                if rest.func == sp.exp:
                    if e_term is not None:
                        return None
                    e_term = ('exp', rest)
                    e_coeff = int(coeff) if coeff.is_Integer else float(coeff)
                elif isinstance(rest, sp.Pow) and rest.args[0] == sp.E:
                    if e_term is not None:
                        return None
                    e_term = ('pow', rest)
                    e_coeff = int(coeff) if coeff.is_Integer else float(coeff)
                else:
                    return None
            elif isinstance(arg, sp.Pow) and arg.args[0] == sp.E:
                if e_term is not None:
                    return None
                e_term = ('pow', arg)
            else:
                return None

        if e_term is None:
            return None

        e_kind, e_obj = e_term
        if e_kind == 'exp':
            exp_arg = e_obj.args[0]
        else:
            exp_arg = e_obj.args[1]

        k_raw, var_part = exp_arg.as_coeff_Mul()
        if var_part != x:
            if isinstance(var_part, sp.Mul) and len(var_part.args) == 2:
                if var_part.args[0] == -1 and var_part.args[1] == x:
                    k_raw = -k_raw
                else:
                    return None
            else:
                return None

        has_minus_one = constant is not None and constant < 0

        return {
            'has_minus_one': has_minus_one,
            'k': k_raw,
            'a': e_coeff,
            'constant': constant,
        }

    def _extract_e_terms(self, expr):
        """Extract all e^{kx} terms from an Add expression.
        Returns list of (sign, k) tuples, or None if non-e terms found."""
        x = self.var
        if not isinstance(expr, sp.Add):
            return None
        e_terms = []
        for arg in expr.args:
            if arg.func == sp.exp:
                exp_arg = arg.args[0]
                k, var_part = exp_arg.as_coeff_Mul()
                if var_part == x:
                    e_terms.append((1, k))
                elif isinstance(var_part, sp.Mul) and len(var_part.args) == 2 and var_part.args[0] == -1 and var_part.args[1] == x:
                    e_terms.append((1, -k))
                else:
                    return None
            elif isinstance(arg, sp.Mul):
                coeff, rest = arg.as_coeff_Mul()
                if rest.func == sp.exp:
                    exp_arg = rest.args[0]
                    k, var_part = exp_arg.as_coeff_Mul()
                    sign = 1 if coeff > 0 else -1
                    if var_part == x:
                        e_terms.append((sign, k))
                    elif isinstance(var_part, sp.Mul) and len(var_part.args) == 2 and var_part.args[0] == -1 and var_part.args[1] == x:
                        e_terms.append((sign, -k))
                    else:
                        return None
                else:
                    return None
            elif isinstance(arg, sp.Pow) and arg.args[0] == sp.E:
                exp_arg = arg.args[1]
                k, var_part = exp_arg.as_coeff_Mul()
                if var_part == x:
                    e_terms.append((1, k))
                else:
                    return None
            else:
                return None
        return e_terms if e_terms else None

    def _solve_logarithmic_0_over_0(self, expr=None):
        if expr is None:
            expr = self.expr
        self.steps = []
        x, point = self.var, self.point

        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '0/0'),
            'Se sustituye la tendencia de x para hallar la indeterminaciÃ³n.',
            'warning'
        )

        # Extract numerator/denominator from raw expression avoiding
        # as_numer_denom() which normalizes e^{-kx} â†’ 1/e^{kx}
        raw_add = None
        den_factors = []
        if isinstance(expr, sp.Mul):
            for arg in expr.args:
                if isinstance(arg, sp.Add):
                    raw_add = arg
                elif isinstance(arg, sp.Pow) and arg.args[1] == -1:
                    den_factors.append(arg.args[0])
                elif isinstance(arg, sp.Rational):
                    den_factors.append(sp.Integer(arg.q))
        if raw_add is not None and den_factors:
            log_pattern = self._detect_log_numerator(raw_add)
            den = sp.Mul(*den_factors)
        else:
            num, den = expr.as_numer_denom()
            log_pattern = self._detect_log_numerator(num)
        if den == 0:
            den = 1

        if log_pattern is not None and log_pattern['has_minus_one']:
            k = log_pattern['k']
            a = log_pattern['a']

            # Denominator analysis: express den = x * c
            c = 1
            den_over_x_tex = None
            try:
                den_factors = sp.Mul.make_args(den)
                c_val = 1
                found_x = False
                for factor in den_factors:
                    if factor == x:
                        found_x = True
                    elif factor.is_Number:
                        c_val *= factor
                if found_x:
                    c = c_val
                else:
                    den_over_x = sp.simplify(den / x)
                    sub_val = sp.limit(den_over_x, x, self.point)
                    if sub_val.is_Number and sub_val != 0:
                        c_val = sub_val
                        c = sub_val
                        den_over_x_tex = self._latex(den_over_x)
                    else:
                        return self._handle_log_fallback(expr)
            except Exception:
                return self._handle_log_fallback(expr)

            result_val = a * k / c

            limit_tex = self._limit_tex(expr)
            result_tex = self._latex(result_val)
            k_tex = self._latex(k)
            c_tex = self._latex(c)
            abs_k_tex = self._latex(abs(k))

            special_limit_tex = '\\lim_{u \\to 0} \\frac{e^{u} - 1}{u} = 1'

            lines = []
            lines.append(f'\\text{{Se multiplica y divide por }}{abs_k_tex}:')

            # Build kx string (use sign-aware display)
            kx_str = f'{k_tex}{x}' if k != 1 and k != -1 else (str(x) if k == 1 else f'-{x}')

            den_tex = self._latex(den)
            if den_over_x_tex:
                display_den_tex = f'x \\cdot \\left({den_over_x_tex}\\right)'
            else:
                display_den_tex = den_tex

            kc_frac = f'\\frac{{{k_tex}}}{{{c_tex}}}'
            result_prefix = f'{a} \\cdot {kc_frac}' if a != 1 else kc_frac

            if a == 1:
                transform = (
                    f'\\frac{{e^{{{kx_str}}} - 1}}{{{display_den_tex}}}'
                    f' = {kc_frac}'
                    f' \\cdot \\frac{{e^{{{kx_str}}} - 1}}{{{kx_str}}}'
                )
            else:
                transform = (
                    f'\\frac{{{a} \\left(e^{{{kx_str}}} - 1\\right)}}{{{display_den_tex}}}'
                    f' = {a} \\cdot {kc_frac}'
                    f' \\cdot \\frac{{e^{{{kx_str}}} - 1}}{{{kx_str}}}'
                )
            lines.append(transform)

            lines.append(
                f'{limit_tex} = {result_prefix}'
                f' \\cdot {{\\color{{green}}{special_limit_tex}}}'
                f' = {result_tex}'
            )

            paso2_tex = ' \\\\ '.join(lines)
            paso2_tex = paso2_tex + ' \\\\ ' + f'\\boxed{{{limit_tex} = {result_tex}}}'

            self._add_step(
                'Paso 2',
                paso2_tex,
                f'Se multiplica y divide por {abs_k_tex}.',
                'info'
            )

            return result_val

        if log_pattern is not None and not log_pattern['has_minus_one']:
            k = log_pattern['k']
            k_tex = self._latex(k)
            kx_str = f'{k_tex}{x}' if k != 1 else str(x)

            lines = []
            lines.append(f'\\text{{Se suma y se resta uno:}}')
            num_tex = self._latex(raw_add if raw_add is not None else num)
            e_term_tex = f'e^{{{kx_str}}}'
            lines.append(
                f'{num_tex} = ({e_term_tex} - 1) + 1'
            )

            paso2_tex = ' \\\\ '.join(lines)
            self._add_step(
                'Paso 2',
                paso2_tex,
                f'Se suma y se resta uno.',
                'info'
            )

            sympy_limit = self._solve_silent(expr)
            if sympy_limit is not None and not self._is_indeterminate(sympy_limit):
                result_tex = self._latex(sympy_limit)
                paso2_tex = paso2_tex + ' \\\\ ' + f'\\boxed{{{self._limit_tex(expr)} = {result_tex}}}'
                self.steps[-1]['tex'] = paso2_tex
                return sympy_limit

        # Multi e-term pattern (e^{ax} Â± e^{bx} ...) without -1
        e_terms = self._extract_e_terms(raw_add if raw_add is not None else num)
        if e_terms and len(e_terms) >= 2:
            limit_tex = self._limit_tex(expr)
            lines = []
            lines.append(f'\\text{{Se suma y se resta uno:}}')

            raw_add_tex = self._latex(raw_add if raw_add is not None else num)
            den_tex = self._latex(den)

            # Sort e_terms: positive signs first for display
            e_terms_sorted = sorted(e_terms, key=lambda t: -t[0])

            # Build: e^{5x} - e^{-2x} = (e^{5x} - 1) - (e^{-2x} - 1)
            transformed_parts = []
            for i, (sign, k) in enumerate(e_terms_sorted):
                k_tex = self._latex(k)
                kx_str = f'{k_tex}{x}' if k != 1 else str(x)
                part = f'(e^{{{kx_str}}} - 1)'
                if i == 0:
                    transformed_parts.append(part if sign == 1 else '- ' + part)
                else:
                    transformed_parts.append('+ ' + part if sign == 1 else '- ' + part)

            transformed_tex = ' '.join(transformed_parts)
            lines.append(f'{raw_add_tex} = {transformed_tex}')

            # Denominator analysis for c: find c such that den = c * x
            try:
                den_c = sp.simplify(den / x)
                c_val = sp.limit(den_c, x, self.point)
                if c_val == 0 or c_val is None:
                    c_val = 1
            except:
                c_val = 1
            c_tex = self._latex(c_val)

            special_limit_tex = '\\lim_{u \\to 0} \\frac{e^{u} - 1}{u} = 1'

            # Show individual term limits with multiply/divide by |k|
            term_lines = []
            for sign, k in e_terms_sorted:
                k_tex = self._latex(k)
                kx_str = f'{k_tex}{x}' if k != 1 else str(x)
                abs_k = abs(k)
                abs_k_tex = self._latex(abs_k)
                # (e^{kx} - 1) / den = k/c * (e^{kx} - 1)/(kx)
                kc_frac = f'\\frac{{{k_tex}}}{{{c_tex}}}'
                sign_str = '' if sign == 1 else '-'
                if sign == 1:
                    term_lines.append(
                        f'\\frac{{e^{{{kx_str}}} - 1}}{{{den_tex}}}'
                        f' = {kc_frac}'
                        f' \\cdot \\frac{{e^{{{kx_str}}} - 1}}{{{kx_str}}}'
                    )
                else:
                    term_lines.append(
                        f'-\\frac{{e^{{{kx_str}}} - 1}}{{{den_tex}}}'
                        f' = -{kc_frac}'
                        f' \\cdot \\frac{{e^{{{kx_str}}} - 1}}{{{kx_str}}}'
                    )

            lines.append('')
            for tl in term_lines:
                lines.append(tl)

            # Combine with green limit
            combined_parts = []
            for sign, k in e_terms_sorted:
                eff = sign * k / c_val
                eff_tex = self._latex(eff)
                if eff >= 0:
                    combined_parts.append(
                        f'{eff_tex} \\cdot {{\\color{{green}}{special_limit_tex}}}'
                    )
                else:
                    combined_parts.append(
                        f'\\left({eff_tex}\\right) \\cdot {{\\color{{green}}{special_limit_tex}}}'
                    )

            # Compute result
            result_val = sum(sign * k / c_val for sign, k in e_terms)
            result_tex = self._latex(result_val)

            lines.append(
                f'{limit_tex} = {" + ".join(combined_parts)}'
            )

            # Show arithmetic: 5 - (-2) = 7
            arith_parts = []
            for sign, k in e_terms_sorted:
                eff = sign * k / c_val
                arith_parts.append(self._latex(eff))
            arith_tex = ' + '.join(arith_parts)
            if arith_tex != result_tex:
                lines.append(f'= {arith_tex}')
            lines.append(f'= {result_tex}')

            paso2_tex = ' \\\\ '.join(lines)
            paso2_tex = paso2_tex + ' \\\\ ' + f'\\boxed{{{limit_tex} = {result_tex}}}'

            self._add_step(
                'Paso 2',
                paso2_tex,
                'Se suma y se resta uno para aplicar el lÃ­mite fundamental.',
                'info'
            )

            return result_val

        return self._solve_log_mixed_terms(expr, raw_add if raw_add is not None else num, den)

    def _solve_log_mixed_terms(self, expr, raw_num, den):
        """Handle mixed e^{p(x)} + trig/other terms by splitting into known limits.
        E.g., (e^{x^2} - cos(x))/x^2 = (e^{x^2} - 1)/x^2 + (1 - cos(x))/x^2 = 1 + 1/2 = 3/2"""
        x, point = self.var, self.point
        if not isinstance(raw_num, sp.Add):
            return self._handle_log_fallback(expr)

        # Decompose numerator terms into e-terms and trig terms
        e_data = []  # (coefficient, exponent_arg)
        cos_data = []  # coefficient B for B*cos(x)
        has_other = False
        for term in raw_num.args:
            if term.func == sp.exp:
                e_data.append((1, term.args[0]))
            elif term.is_Mul and len(term.args) == 2 and term.args[0].is_Number and term.args[1].func == sp.exp:
                e_data.append((term.args[0], term.args[1].args[0]))
            elif term.func == sp.cos and term.args[0] == x:
                cos_data.append(1)
            elif term.is_Mul and len(term.args) == 2 and term.args[0].is_Number and term.args[1].func == sp.cos and term.args[1].args[0] == x:
                cos_data.append(term.args[0])
            elif term.is_Number:
                pass  # constant, handled by decomposition
            else:
                has_other = True

        if has_other or (not e_data and not cos_data):
            return self._handle_log_fallback(expr)

        # Verify that constants cancel: sum of coefficients + constant = 0
        e_coeff_sum = sum(c for c, _ in e_data)
        cos_coeff_sum = sum(cos_data)
        # Raw constant terms from the numerator
        const_sum = sum(t for t in raw_num.args if t.is_Number)
        if sp.simplify(e_coeff_sum + cos_coeff_sum + const_sum) != 0:
            return self._handle_log_fallback(expr)

        limit_tex = self._limit_tex(expr)
        den_tex = self._latex(den)
        num_tex = self._latex(raw_num)
        lines = []

        # Show "suma y resta uno" transformation
        # Build: e^{p(x)} - cos(x) = (e^{p(x)} - 1) + (1 - cos(x))
        sum_res_parts = []
        for coeff, exp_arg in e_data:
            sum_res_parts.append(f'(e^{{{self._latex(exp_arg)}}} - 1)')
        for B in cos_data:
            disp_B = sp.simplify(-B)
            if disp_B > 0:
                prefix = f'{self._latex(disp_B)}' if disp_B != 1 else ''
                sum_res_parts.append(f'{prefix}(1 - \\cos({x}))' if prefix else f'(1 - \\cos({x}))')
            elif disp_B < 0:
                prefix = f'{self._latex(-disp_B)}' if -disp_B != 1 else ''
                sum_res_parts.append(f'-{prefix}(1 - \\cos({x}))' if prefix else f'-(1 - \\cos({x}))')
        lines.append(f'\\text{{Se suma y se resta uno:}}')
        lines.append(f'{num_tex} =  ' + '  +  '.join(sum_res_parts))

        # Show the split as fractions
        frac_parts = []
        for coeff, exp_arg in e_data:
            frac_parts.append(f'\\frac{{e^{{{self._latex(exp_arg)}}} - 1}}{{{den_tex}}}')
        for B in cos_data:
            disp_coeff = sp.simplify(-B)
            if disp_coeff > 0:
                prefix = f'{self._latex(disp_coeff)} \\cdot ' if disp_coeff != 1 else ''
                frac_parts.append(f'{prefix}\\frac{{1 - \\cos\\left({x}\\right)}}{{{den_tex}}}')
            elif disp_coeff < 0:
                prefix = f'{self._latex(abs(disp_coeff))} \\cdot ' if abs(disp_coeff) != 1 else ''
                frac_parts.append(f'- {prefix}\\frac{{1 - \\cos\\left({x}\\right)}}{{{den_tex}}}')
        lines.append('  +  '.join(frac_parts))

        term_lines = []
        total = 0

        for coeff, exp_arg in e_data:
            if self._safe_sub(exp_arg) != 0:
                return self._handle_log_fallback(expr)
            ratio = sp.simplify(exp_arg / den)
            c = sp.limit(ratio, x, point) if ratio.has(x) else ratio
            if c == 0 or c is None:
                return self._handle_log_fallback(expr)
            ea_tex = self._latex(exp_arg)
            c_tex = self._latex(c)
            e_tex = f'e^{{{ea_tex}}}'
            term_lines.append(
                f'\\frac{{{e_tex} - 1}}{{{den_tex}}}'
                f' = {c_tex} \\cdot \\frac{{{e_tex} - 1}}{{{ea_tex}}}'
                f' = {c_tex} \\cdot 1 = {c_tex}'
            )
            total += coeff * c

        for B in cos_data:
            # B*cos(x) â†’ B*(cos(x)-1) contribution = -B*(1-cos(x))
            cos_1_den = sp.simplify((1 - sp.cos(x)) / den)
            c1 = sp.limit(cos_1_den, x, point)
            if c1 == 0 or c1 is None:
                return self._handle_log_fallback(expr)
            contrib = sp.simplify(-B * c1)
            c1_tex = self._latex(c1)
            disp_B = sp.simplify(-B)
            disp_contrib = sp.simplify(contrib)
            if disp_B == 1:
                term_lines.append(
                    f'\\frac{{1 - \\cos({x})}}{{{den_tex}}} = {c1_tex}'
                )
            elif disp_B == -1:
                term_lines.append(
                    f'-\\frac{{1 - \\cos({x})}}{{{den_tex}}} = {self._latex(contrib)}'
                )
            else:
                term_lines.append(
                    f'{self._latex(disp_B)} \\cdot \\frac{{1 - \\cos({x})}}{{{den_tex}}}'
                    f' = {self._latex(contrib)}'
                )
            total += contrib

        lines.extend(term_lines)
        res = sp.simplify(total)
        if not self._is_indeterminate(res):
            paso2_tex = ' \\\\ '.join(lines)
            paso2_tex += ' \\\\ ' + f'\\boxed{{{limit_tex} = {self._latex(res)}}}'
            self._add_step(
                'Paso 2',
                paso2_tex,
                'Se descompone la expresiÃ³n en lÃ­mites fundamentales.',
                'info'
            )
            return res

        return self._handle_log_fallback(expr)

    def _handle_log_fallback(self, expr):
        sympy_limit = self._solve_silent(expr)
        if sympy_limit is not None and not self._is_indeterminate(sympy_limit):
            result_tex = self._latex(sympy_limit)
            paso2_tex = f'\\boxed{{{self._limit_tex(expr)} = {result_tex}}}'
            self._add_step(
                'Paso 2',
                paso2_tex,
                'Se halla el lÃ­mite.',
                'info'
            )
            return sympy_limit

        return self._solve_fallback(expr)

    def _solve_0_over_0_detailed(self, expr=None):
        if expr is None:
            expr = self.expr
        self.steps = []
        x, point = self.var, self.point

        # Route to specific solvers based on limit type
        if self._limit_type == 'trigonomÃ©trico':
            return self._solve_trigonometric_0_over_0(expr)
        if self._limit_type == 'logarÃ­tmico':
            return self._solve_logarithmic_0_over_0(expr)

        # Default: rational / irrational path
        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '0/0'),
            'Se sustituye la tendencia de x para hallar la indeterminaciÃ³n.',
            'warning'
        )

        num, den = expr.as_numer_denom()
        is_irracional = self._limit_type == 'algebraico irracional'

        # Try root substitution before factor/rationalize (e.g., (x^(1/n)-a)/(x-a))
        root_result = self._try_root_substitution(num, den, expr)
        if root_result is not None:
            return root_result

        simplified = None
        val = None
        result_type = None
        factor_info = None
        rat_info = None

        try_paths = ['factor', 'rationalize'] if not is_irracional else ['rationalize', 'factor']

        for path in try_paths:
            if path == 'factor':
                r = self._factor_with_info(num, den)
                if r is not None:
                    simplified, val, factor_info = r
                    result_type = 'factor'
                    break
            elif path == 'rationalize':
                r = self._rationalize_with_info(num, den)
                if r is not None:
                    simplified, val, rat_info = r
                    result_type = 'rationalize'
                    break

        if result_type == 'factor' and factor_info is not None:
            num_tex = sp.latex(factor_info['num_factored']) if factor_info['num_changed'] else sp.latex(factor_info['num_original'])
            den_tex = sp.latex(factor_info['den_factored']) if factor_info['den_changed'] else sp.latex(factor_info['den_original'])
            orig_frac = f"\\frac{{{sp.latex(num)}}}{{{sp.latex(den)}}}"
            factored_frac = f"\\frac{{{num_tex}}}{{{den_tex}}}"
            simpl_tex = sp.latex(simplified)

            parts = []
            if factor_info['num_changed']:
                t = factor_info['num_type']
                parts.append(f"numerador ({t})" if t else "numerador")
            if factor_info['den_changed']:
                t = factor_info['den_type']
                parts.append(f"denominador ({t})" if t else "denominador")
            desc = f"Se factoriza el {parts[0]} y el {parts[1]}" if len(parts) == 2 else f"Se factoriza el {parts[0]}"

            step2_tex = f"{orig_frac} = {factored_frac} \\\\ {factored_frac} = {simpl_tex}"
            self._add_step('Paso 2', step2_tex, desc, 'info')

            sub_tex = self._substitution_tex(simplified)
            if sub_tex:
                step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {simpl_tex} = {sub_tex} = {self._latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}"
            else:
                step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {simpl_tex} = {self._latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}"
            self._add_step('Paso 3', step3_tex, 'Se sustituye el valor de la tendencia de x para hallar el lÃ­mite.', 'info')
            return val

        if result_type == 'rationalize' and rat_info is not None:
            what = 'numerador y el denominador' if rat_info.get('both') else ('numerador' if rat_info['is_num'] else 'denominador')
            expr_tex = self._latex(expr)
            if isinstance(expr, sp.Add):
                expr_tex = f'\\left({expr_tex}\\right)'
            conj_tex = self._latex(rat_info['conj'])
            new_tex = self._latex(simplified)
            if rat_info.get('both') and rat_info.get('conj2'):
                conj2_tex = self._latex(rat_info['conj2'])
                step2_tex = f"{expr_tex} \\cdot \\frac{{{conj_tex}}}{{{conj_tex}}} \\cdot \\frac{{{conj2_tex}}}{{{conj2_tex}}} = {new_tex}"
            else:
                step2_tex = f"{expr_tex} \\cdot \\frac{{{conj_tex}}}{{{conj_tex}}} = {new_tex}"
            self._add_step('Paso 2', step2_tex, f'Se racionaliza el {what} para eliminar la indeterminaciÃ³n.', 'info')

            sub_tex = self._substitution_tex(simplified)
            if sub_tex:
                step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {new_tex} = {sub_tex} = {self._latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}"
            else:
                step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {new_tex} = {self._latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}"
            self._add_step('Paso 3', step3_tex, 'Se sustituye el valor de la tendencia de x para hallar el lÃ­mite.', 'info')
            return val

        lh_result = self._try_lhopital(expr)
        if lh_result is not None:
            return lh_result
        return self._solve_fallback(expr)

    def _solve_0_over_0(self, expr=None):
        if expr is None:
            expr = self.expr
        frac = together(expr)
        num, den = fraction(frac)

        is_irracional = self._limit_type == 'algebraico irracional'

        if is_irracional:
            rational_result = self._try_rationalize(num, den)
            if rational_result is not None:
                return rational_result
            factor_result = self._try_factor(num, den)
            if factor_result is not None:
                return factor_result
        else:
            factor_result = self._try_factor(num, den)
            if factor_result is not None:
                return factor_result
            rational_result = self._try_rationalize(num, den)
            if rational_result is not None:
                return rational_result

        lh_result = self._try_lhopital(expr)
        if lh_result is not None:
            return lh_result
        return self._solve_fallback(expr)

    def _try_root_substitution(self, num, den, expr):
        """Handle limits like (x^(1/n) - a^(1/n)) / (x - a) using root factorization."""
        x, point = self.var, self.point
        if point in (oo, -oo, zoo):
            return None
        # Check denominator: x - point or point - x or k*(x - point)
        den_poly = sp.expand(den)
        if not den_poly.is_polynomial(x) or sp.degree(den_poly, x) != 1:
            return None
        den_coeffs = sp.Poly(den_poly, x).all_coeffs()
        if len(den_coeffs) != 2:
            return None
        a1, a0 = den_coeffs  # a1*x + a0
        if a1 == 0:
            return None
        root_val = -a0 / a1
        if sp.simplify(root_val - point) != 0:
            return None
        # Denominator is k*(x - point). Extract k.
        k = a1
        # Check numerator: difference of roots
        num_expanded = sp.expand(num)
        if not num_expanded.is_Add or len(num_expanded.args) != 2:
            return None
        # Look for term of the form x^(1/n) and a constant term
        terms = list(num_expanded.args)
        root_term = None
        const_term = None
        for t in terms:
            if t.is_Pow and t.args[0] == x and isinstance(t.args[1], sp.Rational) and t.args[1].q > 1:
                root_term = t
            elif t.is_Number or (t.is_Symbol and not t.has(x)):
                const_term = t
            elif t.is_Mul and len(t.args) == 2 and isinstance(t.args[0], sp.Integer) and t.args[1].is_Pow:
                # Handle -2*x^(1/3) etc
                if t.args[1].is_Pow and t.args[1].args[0] == x and isinstance(t.args[1].args[1], sp.Rational) and t.args[1].args[1].q > 1:
                    root_term = t
            elif isinstance(t, sp.Mul):
                for arg in t.args:
                    if arg.is_Pow and arg.args[0] == x and isinstance(arg.args[1], sp.Rational) and arg.args[1].q > 1:
                        root_term = t
                        break
        if root_term is None or const_term is None:
            return None
        # Extract the root exponent q (denominator of the rational exponent)
        try:
            if root_term.is_Pow:
                exp_root = root_term.args[1]
            elif root_term.is_Mul:
                for arg in root_term.args:
                    if arg.is_Pow and arg.args[0] == x:
                        exp_root = arg.args[1]
                        break
                else:
                    return None
            else:
                return None
        except:
            return None
        if not isinstance(exp_root, sp.Rational):
            return None
        n = exp_root.q  # denominator of the exponent
        if n < 2 or n > 10:
            return None
        # Verify the numerator is 0 at the point
        if not self._is_zero(self._safe_sub(num)):
            return None
        # Construct the factorization: x - a = (x^(1/n) - a^(1/n)) * sum_{i=0}^{n-1} x^(i/n) * a^((n-1-i)/n)
        a_root = point ** sp.Rational(1, n)
        # Build the expanded denominator: (x - point)
        # The factored form: (x^(1/n) - point^(1/n)) * (x^((n-1)/n) + x^((n-2)/n)*point^(1/n) + ... + point^((n-1)/n))
        sum_term = 0
        for i in range(n):
            sum_term += (x ** sp.Rational(n-1-i, n)) * (a_root ** i)
        sum_term = sp.simplify(sum_term)
        sign = 1
        if sp.expand(num).coeff(x**exp_root) < 0:
            sign = -1
        # Simplified expression after cancellation
        simplified = sp.simplify(sign / (k * sum_term))
        val = self._safe_sub(simplified)
        if self._is_indeterminate(val):
            return None
        orig_frac = sp.latex(expr)
        simpl_tex = sp.latex(simplified)
        step2_tex = f"\\frac{{{sp.latex(num)}}}{{{sp.latex(den)}}} = \\frac{{{sp.latex(num)}}}{{({sp.latex(root_term)})({sp.latex(sum_term)})}} = {simpl_tex}"
        self._add_step('Paso 2', step2_tex, f'Se factoriza el denominador usando diferencia de potencias {n}-Ã©simas.', 'info')
        sub_tex = self._substitution_tex(simplified)
        if sub_tex:
            step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {simpl_tex} = {sub_tex} = {sp.latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {sp.latex(val)}}}"
        else:
            step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {simpl_tex} = {sp.latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {sp.latex(val)}}}"
        self._add_step('Paso 3', step3_tex, 'Se sustituye el valor de la tendencia de x para hallar el lÃ­mite.', 'info')
        return val

    def _try_factor(self, num, den):
        x, point = self.var, self.point
        num_f = factor(num)
        den_f = factor(den)
        if num_f != num or den_f != den:
            orig = sp.simplify(num / den)
            factored = sp.simplify(num_f / den_f)
            which = 'numerador' if num_f != num else 'denominador' if den_f != den else 'ambos'
            self._add_step(
                'FactorizaciÃ³n',
                f'\\frac{{{self._latex(num)}}}{{{self._latex(den)}}} = \\frac{{{self._latex(num_f)}}}{{{self._latex(den_f)}}}',
                f'Se factoriza {which} para eliminar la indeterminaciÃ³n.',
                'info'
            )
            simplified = cancel(num_f / den_f)
            if simplified != factored:
                self._add_step(
                    'CancelaciÃ³n',
                    f'\\frac{{{self._latex(num_f)}}}{{{self._latex(den_f)}}} = {self._latex(simplified)}',
                    'Cancelamos los factores comunes.',
                    'info'
                )
            val = self._safe_sub(simplified)
            if not self._is_indeterminate(val):
                self._add_step(
                    'EvaluaciÃ³n',
                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(simplified)} = {self._latex(val)}',
                    f'Se sustituye el valor de la tendencia de {x.name} para hallar el lÃ­mite.',
                    'info'
                )
                return val
        return None

    def _try_rationalize(self, num, den):
        x, point = self.var, self.point
        target = None
        is_num = False
        if self._contains_sqrt(num):
            target = num
            is_num = True
        elif self._contains_sqrt(den):
            target = den
            is_num = False
        else:
            return None
        conj = self._rationalizing_conjugate(target)
        if conj is None or conj == target:
            return None
        expr = num / den
        if is_num:
            new_num = sp.expand(num * conj)
            new_den = den * conj
        else:
            new_num = sp.expand(num * conj)
            new_den = den * conj
        what = 'numerador' if is_num else 'denominador'
        self._add_step(
            'RacionalizaciÃ³n',
            f'{self._latex(expr)} \\cdot \\frac{{{self._latex(conj)}}}{{{self._latex(conj)}}}',
            f'Se racionaliza el {what} para eliminar la indeterminaciÃ³n.',
            'info'
        )
        new_expr = sp.cancel(new_num / new_den)
        self._add_step(
            'SimplificaciÃ³n',
            f'{self._latex(new_expr)}',
            'Simplificamos la expresiÃ³n resultante.',
            'info'
        )
        val = self._safe_sub(new_expr)
        if not self._is_indeterminate(val):
            self._add_step(
                'EvaluaciÃ³n',
                f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {self._latex(val)}',
                f'Se sustituye el valor de la tendencia de {x.name} para hallar el lÃ­mite.',
                'info'
            )
            return val
        return self._solve_0_over_0_sub(*fraction(together(new_expr)))

    def _solve_0_over_0_sub(self, num, den):
        r = self._try_factor(num, den)
        if r is not None:
            return r
        return self._try_lhopital(num / den)

    def _try_lhopital(self, expr, max_iter=5):
        x, point = self.var, self.point
        current = expr
        applied = False
        for i in range(max_iter):
            frac = together(current)
            n, d = fraction(frac)
            n_d = diff(n, x)
            d_d = diff(d, x)
            if self._safe_sub(d_d) == 0 or d_d == 0:
                return None
            new_expr = sp.simplify(n_d / d_d)
            labels = {1: 'primera', 2: 'segunda', 3: 'tercera', 4: 'cuarta', 5: 'quinta'}
            lbl = labels.get(i + 1, f'{i+1}Âª')
            self._add_step(
                f'L\'HÃ´pital ({lbl} aplicaciÃ³n)',
                f'\\begin{{aligned}} f\'(x) &= {self._latex(n_d)} \\\\ g\'(x) &= {self._latex(d_d)} \\\\ \\frac{{f\'(x)}}{{g\'(x)}} &= {self._latex(new_expr)} \\end{{aligned}}',
                'Derivamos numerador y denominador por separado.',
                'info'
            )
            applied = True
            val = self._safe_sub(new_expr)
            if not self._is_indeterminate(val):
                return val
            current = new_expr
        if applied:
            self._add_step(
                'L\'HÃ´pital',
                f'\\text{{Se alcanzÃ³ el mÃ¡ximo de iteraciones ({max_iter}).}}',
                '',
                'warning'
            )
        return None

    def _solve_inf_over_inf_detailed(self, expr=None):
        if expr is None:
            expr = self.expr
        self.steps = []
        x, point = self.var, self.point
        limit_tex_full = self._limit_tex(expr)

        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '\\infty/\\infty'),
            'Se sustituye la tendencia de x para hallar la indeterminaciÃ³n.',
            'warning'
        )

        frac = together(expr)
        num, den = fraction(frac)
        try:
            n_deg = degree(num, x) if num.has(x) else 0
            d_deg = degree(den, x) if den.has(x) else 0
        except:
            n_deg = None

        if n_deg is not None and n_deg >= 0 and d_deg >= 0:
            highest = max(n_deg, d_deg)
            xh = x ** highest
            new_num = expand(num / xh)
            new_den = expand(den / xh)
            highest_tex = self._latex(xh)

            val = self._safe_sub(new_num / new_den)
            new_expr = sp.simplify(new_num / new_den)

            self._add_step(
                'Paso 2',
                f'\\frac{{{self._latex(num)}}}{{{self._latex(den)}}} = \\frac{{{self._latex(new_num)}}}{{{self._latex(new_den)}}}',
                f'Se divide la expresiÃ³n entre {highest_tex}',
                'info'
            )

            if not self._is_indeterminate(val):
                substituted_after_tex = self._substitute_point_tex(new_expr)
                self._add_step(
                    'Paso 3',
                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {substituted_after_tex} = {self._latex(val)} \\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}',
f'Sustituimos {x.name} = {self._point_tex()} en la expresiÃ³n simplificada para obtener el valor final.',
                    'info'
                )
                return val

        lh = self._try_lhopital(expr)
        if lh is not None:
            return lh
        return self._solve_fallback(expr)

    def _solve_inf_over_inf(self, expr=None):
        if expr is None:
            expr = self.expr
        x, point = self.var, self.point
        frac = together(expr)
        num, den = fraction(frac)
        try:
            n_deg = degree(num, x) if num.has(x) else 0
            d_deg = degree(den, x) if den.has(x) else 0
        except:
            n_deg = None
        if n_deg is not None and n_deg >= 0 and d_deg >= 0:
            highest = max(n_deg, d_deg)
            xh = x ** highest
            new_num = expand(num / xh)
            new_den = expand(den / xh)
            val = self._safe_sub(new_num / new_den)
            new_expr = sp.simplify(new_num / new_den)
            self._add_step(
                'DivisiÃ³n por mÃ¡xima potencia',
                f'\\frac{{{self._latex(num)}}}{{{self._latex(den)}}} = \\frac{{{self._latex(new_num)}}}{{{self._latex(new_den)}}}',
                f'Se divide la expresiÃ³n entre {self._latex(xh)}',
                'info'
            )
            if not self._is_indeterminate(val):
                substituted_after = new_expr.subs(x, self.point)
                substituted_after_tex = self._latex(substituted_after)
                self._add_step(
                    'EvaluaciÃ³n',
                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {substituted_after_tex} = {self._latex(val)}',
                    f'Sustituimos {x.name} = {self._point_tex()} en la expresiÃ³n simplificada.',
                    'info'
                )
                return val
        lh = self._try_lhopital(expr)
        if lh is not None:
            return lh
        return self._solve_fallback(expr)

    def _solve_0_times_inf(self, expr=None):
        if expr is None:
            expr = self.expr
        zero_factor = None
        inf_factor = None
        for arg in expr.args:
            v = self._safe_sub(arg)
            if self._is_zero(v):
                zero_factor = arg
            elif self._is_inf(v):
                inf_factor = arg
        if zero_factor is not None and inf_factor is not None:
            x, point = self.var, self.point
            from sympy import diff

            def try_lhopital_on_factors(f_num, f_den, label):
                """Apply L'HÃ´pital treating f_num/f_den as the quotient."""
                n_d = diff(f_num, x)
                d_d = diff(f_den, x)
                if self._safe_sub(d_d) == 0 or d_d == 0:
                    return None
                new_rat = sp.simplify(n_d / d_d)
                self._add_step(
                    f'L\'HÃ´pital ({label})',
                    f'\\begin{{aligned}} f\'(x) &= {self._latex(n_d)} \\\\ g\'(x) &= {self._latex(d_d)} \\\\ \\frac{{f\'(x)}}{{g\'(x)}} &= {self._latex(new_rat)} \\end{{aligned}}',
                    'Derivamos numerador y denominador por separado.',
                    'info'
                )
                val = self._safe_sub(new_rat)
                if not self._is_indeterminate(val):
                    return val
                # Try one more iteration
                if sp.together(new_rat) != new_rat:
                    n2, d2 = sp.fraction(sp.together(new_rat))
                    if d2 != 1:
                        n2_d = diff(n2, x)
                        d2_d = diff(d2, x)
                        if self._safe_sub(d2_d) != 0 and d2_d != 0:
                            new_rat2 = sp.simplify(n2_d / d2_d)
                            self._add_step(
                                'L\'HÃ´pital (segunda aplicaciÃ³n)',
                                f'\\begin{{aligned}} f\'(x) &= {self._latex(n2_d)} \\\\ g\'(x) &= {self._latex(d2_d)} \\\\ \\frac{{f\'(x)}}{{g\'(x)}} &= {self._latex(new_rat2)} \\end{{aligned}}',
                                'Derivamos numerador y denominador nuevamente.',
                                'info'
                            )
                            val2 = self._safe_sub(new_rat2)
                            if not self._is_indeterminate(val2):
                                return val2
                return None

            # Try 0/0 form: zero / (1/inf)  â†’ numerator: zero, denominator: 1/inf
            self._add_step(
                'TransformaciÃ³n a 0/0',
                f'{self._latex(expr)} = \\frac{{{self._latex(zero_factor)}}}{{\\frac{{1}}{{{self._latex(inf_factor)}}}}}',
                'Reescribimos como cociente para aplicar L\'HÃ´pital.',
                'info'
            )
            f_den_1 = sp.Pow(inf_factor, -1)  # 1/inf_factor
            # Don't simplify / together / fraction - apply L'HÃ´pital directly on the pair
            result = try_lhopital_on_factors(zero_factor, f_den_1, '0/0')
            if result is not None:
                return result

            # Try âˆž/âˆž form: inf / (1/zero) â†’ numerator: inf, denominator: 1/zero
            self._add_step(
                'TransformaciÃ³n a âˆž/âˆž',
                f'{self._latex(expr)} = \\frac{{{self._latex(inf_factor)}}}{{\\frac{{1}}{{{self._latex(zero_factor)}}}}}',
                'Reescribimos como cociente para aplicar L\'HÃ´pital.',
                'info'
            )
            f_den_2 = sp.Pow(zero_factor, -1)  # 1/zero_factor
            result = try_lhopital_on_factors(inf_factor, f_den_2, 'âˆž/âˆž')
            if result is not None:
                return result

        return self._solve_fallback(expr)

    def _solve_inf_minus_inf_detailed(self, expr=None):
        if expr is None:
            expr = self.expr
        self.steps = []
        x, point = self.var, self.point
        orig_tex = self._latex(expr)
        limit_tex_full = self._limit_tex(expr)

        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '\\infty - \\infty'),
            'Se sustituye la tendencia de x para hallar la indeterminaciÃ³n.',
            'warning'
        )

        has_radicals = self._contains_sqrt(expr)

        if has_radicals:
            frac = together(expr)
            n, d = fraction(frac)
            r = self._rationalize_with_info(n, d)
            if r is not None:
                new_expr, val, rat_info = r
                conj_tex = self._latex(rat_info['conj'])
                what = 'numerador' if rat_info['is_num'] else 'denominador'
                paren_tex = f'\\left({orig_tex}\\right)' if isinstance(expr, sp.Add) else orig_tex
                self._add_step(
                    'Paso 2',
                    f'{paren_tex} \\cdot \\frac{{{conj_tex}}}{{{conj_tex}}} = {self._latex(new_expr)}',
                    f'Se racionaliza el {what}.',
                    'info'
                )
                if not self._is_indeterminate(val):
                    self._add_step(
                        'Paso 3',
                        f'\\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}',
                        'Se halla el lÃ­mite.',
                        'info'
                    )
                    return val
                # After rationalization, still indeterminate: compute limit directly
                try:
                    final_val = sp.limit(new_expr, x, point)
                    if not self._is_indeterminate(final_val):
                        self._add_step(
                            'Paso 3',
                            f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {self._latex(final_val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(final_val)}}}',
                            'Se calcula el lÃ­mite de la expresiÃ³n resultante.',
                            'info'
                        )
                        return final_val
                except:
                    pass
            else:
                # Manual rationalization for sqrt Add
                if self._contains_sqrt(expr) and isinstance(expr, sp.Add):
                    conj = self._rationalizing_conjugate(expr)
                    if conj is not None:
                        paren_tex = f'\\left({orig_tex}\\right)'
                        conj_tex = self._latex(conj)
                        new_num = sp.expand(expr * conj)
                        new_den = conj
                        new_expr = sp.cancel(new_num / new_den)
                        self._add_step(
                            'Paso 2',
                            f'{paren_tex} \\cdot \\frac{{{conj_tex}}}{{{conj_tex}}} = {self._latex(new_expr)}',
                            'Se racionaliza la expresiÃ³n.',
                            'info'
                        )
                        val = self._safe_sub(new_expr)
                        if not self._is_indeterminate(val):
                            self._add_step(
                                'Paso 3',
                                f'\\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}',
                                'Se halla el lÃ­mite.',
                                'info'
                            )
                            return val
                        # Still indeterminate: compute limit directly
                        try:
                            final_val = sp.limit(new_expr, x, point)
                            if not self._is_indeterminate(final_val):
                                self._add_step(
                                    'Paso 3',
                                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {self._latex(final_val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(final_val)}}}',
                                    'Se calcula el lÃ­mite de la expresiÃ³n resultante.',
                                    'info'
                                )
                                return final_val
                        except:
                            pass
        else:
            frac = together(expr)
            if frac != expr:
                self._add_step(
                    'Paso 2',
                    f'{orig_tex} = {self._latex(frac)}',
                    'Se restan fracciones.',
                    'info'
                )
                val = self._safe_sub(frac)
                if not self._is_indeterminate(val):
                    self._add_step(
                        'Paso 3',
                        f'\\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}',
                        'Se sustituye el valor de la tendencia de x para hallar el lÃ­mite.',
                        'info'
                    )
                    return val
                form = self._detect_form(frac)
                if form == '0/0':
                    n, d = fraction(frac)
                    factor_r = self._factor_with_info(n, d)
                    if factor_r is not None:
                        _, sub_val, _ = factor_r
                        self._add_step(
                            'Paso 3',
                            f'\\boxed{{{self._limit_tex(expr)} = {self._latex(sub_val)}}}',
                            'Se sustituye el valor de la tendencia de x para hallar el lÃ­mite.',
                            'info'
                        )
                        return sub_val
                    lh = self._try_lhopital(frac)
                    if lh is not None:
                        return lh
                elif form == 'âˆž/âˆž':
                    num, den = fraction(frac)
                    try:
                        n_deg = degree(num, x) if num.has(x) else 0
                        d_deg = degree(den, x) if den.has(x) else 0
                    except:
                        n_deg = None
                    if n_deg is not None and n_deg >= 0 and d_deg >= 0:
                        highest = max(n_deg, d_deg)
                        xh = x ** highest
                        new_num = expand(num / xh)
                        new_den = expand(den / xh)
                        sub_val = self._safe_sub(new_num / new_den)
                        if not self._is_indeterminate(sub_val):
                            self._add_step(
                                'Paso 3',
                                f'\\boxed{{{self._limit_tex(expr)} = {self._latex(sub_val)}}}',
                                'Se sustituye el valor de la tendencia de x para hallar el lÃ­mite.',
                                'info'
                            )
                            return sub_val
                    lh = self._try_lhopital(frac)
                    if lh is not None:
                        return lh

        return self._solve_fallback(expr)

    def _solve_inf_minus_inf(self, expr=None):
        if expr is None:
            expr = self.expr
        frac = together(expr)
        if frac != expr:
            self._add_step(
                'CombinaciÃ³n de tÃ©rminos',
                f'{self._latex(expr)} = {self._latex(frac)}',
                'Combinamos los tÃ©rminos en una sola fracciÃ³n.',
                'info'
            )
            val = self._safe_sub(frac)
            if not self._is_indeterminate(val):
                return val
            form = self._detect_form(frac)
            if form == '0/0':
                n, d = fraction(frac)
                return self._solve_0_over_0_sub(n, d)
            if form == 'âˆž/âˆž':
                return self._solve_inf_over_inf(frac)
        n, d = fraction(together(expr))
        r = self._try_rationalize(n, d)
        if r is not None:
            return r
        return self._solve_fallback(expr)

    def _solve_silent(self, expr):
        saved = list(self.steps)
        x = self.var
        result = None
        form = self._detect_form(expr)

        if form == '0/0':
            frac = together(expr)
            num, den = fraction(frac)
            r = self._factor_with_info(num, den)
            if r is not None:
                _, result, _ = r
            if result is None or self._is_indeterminate(result):
                try:
                    lh = self._try_lhopital(frac)
                    if lh is not None and not self._is_indeterminate(lh):
                        result = lh
                except:
                    pass
        elif form == 'âˆž/âˆž':
            num, den = fraction(together(expr))
            try:
                n_deg = degree(num, x) if num.has(x) else 0
                d_deg = degree(den, x) if den.has(x) else 0
            except:
                n_deg = None
            if n_deg is not None and n_deg >= 0 and d_deg >= 0:
                highest = max(n_deg, d_deg)
                xh = x ** highest
                result = self._safe_sub((num / xh) / (den / xh))
            if result is None or self._is_indeterminate(result):
                try:
                    lh = self._try_lhopital(expr)
                    if lh is not None and not self._is_indeterminate(lh):
                        result = lh
                except:
                    pass

        if result is None or self._is_indeterminate(result):
            try:
                if self.direction:
                    result = limit(expr, x, self.point, dir=self.direction)
                else:
                    result = limit(expr, x, self.point)
                result = nsimplify(result)
            except:
                pass

        self.steps = saved
        return result

    def _solve_exponential_detailed(self, form):
        expr = self.expr
        x = self.var
        self.steps = []
        orig_tex = self._latex(expr)
        form_tex = self.FORM_NAMES.get(form, form)

        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, form_tex),
            'Se sustituye la tendencia de x para hallar la indeterminaciÃ³n.',
            'warning'
        )

        if expr.func != Pow:
            return self._solve_fallback(expr)

        base, exponent = expr.args
        f_tex = self._latex(base)
        g_tex = self._latex(exponent)

        # Paso 2 + Paso 3
        if form == '1^âˆž':
            # Use (f-1)Â·g formula
            paso2_tex = (
                f'\\text{{Aplicamos la igualdad: }} '
                f'\\lim \\left({f_tex}\\right)^{{{g_tex}}} = e^{{\\lim ({f_tex}-1) \\cdot {g_tex}}}'
            )
            self._add_step(
                'Paso 2',
                paso2_tex,
                'Se aplica la igualdad fundamental de lÃ­mites exponenciales.',
                'info'
            )

            f_minus_1 = sp.simplify(base - 1)
            new_power = sp.simplify(f_minus_1 * exponent)
            new_power_tex = self._latex(new_power)

            val = self._safe_sub(new_power)
            if not self._is_indeterminate(val):
                result = sp.exp(val)
                paso3_tex = (
                    f'({f_tex}-1) \\cdot {g_tex} = ({self._latex(f_minus_1)}) \\cdot {g_tex} = {new_power_tex} \\\\'
                    f'\\lim \\left({f_tex}\\right)^{{{g_tex}}} = e^{{{new_power_tex}}} = {self._latex(result)} \\\\'
                    f'\\boxed{{{self._limit_tex(expr)} = {self._latex(result)}}}'
                )
                self._add_step('Paso 3', paso3_tex, 'Se halla el lÃ­mite.', 'info')
                return result

        # For âˆž^0, 0^0, or when 1^âˆž formula fails: use gÂ·ln(f) approach
        paso2_formula = self._latex(exponent) + ' \\cdot \\ln\\left(' + f_tex + '\\right)'
        paso2_tex = (
            f'\\text{{Aplicamos logaritmo natural: }} '
            f'\\lim \\left({f_tex}\\right)^{{{g_tex}}} = e^{{\\lim {g_tex} \\cdot \\ln\\left({f_tex}\\right)}}'
        )
        self._add_step(
            'Paso 2',
            paso2_tex,
            'Se aplica logaritmo natural para transformar la exponencial.',
            'info'
        )

        ln_expr = sp.simplify(exponent * sp.log(base))
        ln_tex = self._latex(ln_expr)

        # Try direct evaluation of ln_expr
        ln_val = self._safe_sub(ln_expr)
        if not self._is_indeterminate(ln_val):
            result = sp.exp(ln_val)
            paso3_tex = (
                f'{g_tex} \\cdot \\ln\\left({f_tex}\\right) = {ln_tex} = {self._latex(ln_val)} \\\\'
                f'\\lim \\left({f_tex}\\right)^{{{g_tex}}} = e^{{{self._latex(ln_val)}}} = {self._latex(result)} \\\\'
                f'\\boxed{{{self._limit_tex(expr)} = {self._latex(result)}}}'
            )
            self._add_step('Paso 3', paso3_tex, 'Se halla el lÃ­mite.', 'info')
            return result

        # ln_expr is indeterminate, try to solve via delegation
        paso3_tex = (
            f'{g_tex} \\cdot \\ln\\left({f_tex}\\right) = {ln_tex}'
        )
        self._add_step('Paso 3', paso3_tex, 'Se transforma el lÃ­mite al producto.', 'info')

        result_ln = self._solve_silent(ln_expr)
        if result_ln is not None and not self._is_indeterminate(result_ln):
            L = sp.exp(result_ln)
            self._add_step(
                'Resultado',
                f'\\ln L = {self._latex(result_ln)} \\implies L = e^{{{self._latex(result_ln)}}} = {self._latex(L)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(L)}}}',
                'Se aplica exponencial para hallar el lÃ­mite.',
                'info'
            )
            return L

        return self._solve_fallback(expr)

    def _solve_exponential(self, form):
        x = self.var
        expr = self.expr
        if expr.func != Pow:
            return self._solve_fallback()
        base, exponent = expr.args
        ln_expr = sp.simplify(exponent * log(base))
        self._add_step(
            'TransformaciÃ³n logarÃ­tmica',
            f'\\text{{Sea }} L = {self._latex(expr)} \\\\ \\ln L = {self._latex(exponent)} \\cdot \\ln\\left({self._latex(base)}\\right) = {self._latex(ln_expr)}',
            'Aplicamos logaritmo natural para convertir la exponencial en un producto.',
            'info'
        )
        ln_val = self._safe_sub(ln_expr)
        if not self._is_indeterminate(ln_val):
            L = exp(ln_val)
            self._add_step(
                'ExponenciaciÃ³n',
                f'\\ln L = {self._latex(ln_val)} \\implies L = e^{{{self._latex(ln_val)}}} = {self._latex(L)}',
                'Aplicamos exponencial para despejar L.',
                'info'
            )
            return L
        form_ln = self._detect_form(ln_expr)
        result_ln = None
        if form_ln == '0/0':
            n, d = fraction(together(ln_expr))
            result_ln = self._solve_0_over_0_sub(n, d)
        elif form_ln == 'âˆž/âˆž':
            result_ln = self._solve_inf_over_inf(ln_expr)
        elif form_ln == '0Â·âˆž':
            result_ln = self._solve_0_times_inf(ln_expr)
        else:
            lh = self._try_lhopital(ln_expr)
            if lh is not None:
                result_ln = lh
        if result_ln is not None and not self._is_indeterminate(result_ln):
            L = exp(result_ln)
            self._add_step(
                'ExponenciaciÃ³n',
                f'\\ln L = {self._latex(result_ln)} \\implies L = e^{{{self._latex(result_ln)}}} = {self._latex(L)}',
                'Aplicamos exponencial para despejar L.',
                'info'
            )
            return L
        return self._solve_fallback(expr)

