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
    expr = expr.replace('√', 'sqrt').replace('V(', 'sqrt(').replace('v(', 'sqrt(')
    expr = expr.replace('π', 'pi').replace('∞', 'oo')
    expr = expr.replace('×', '*').replace('·', '*')
    expr = expr.replace('²', '^2').replace('³', '^3').replace('⁴', '^4')
    expr = expr.replace('⁺', '+').replace('⁻', '-')
    expr = expr.replace('−', '-')
    expr = expr.replace('[', '(').replace(']', ')')
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
        base_tex = expr_to_latex(expr.args[0])
        exp = expr.args[1]
        if exp.is_Mul:
            exp_clean = sp.together(exp)
        elif exp.is_Pow and exp.exp == -1:
            exp_clean = sp.together(exp)
        else:
            exp_clean = exp
        exp_tex = expr_to_latex(exp_clean)
        if isinstance(expr.args[0], sp.Add):
            return f'\\left({base_tex}\\right)^{{{exp_tex}}}'
        return f'{base_tex}^{{{exp_tex}}}'
    return latex(expr)


class LimitSolver:
    FORM_NAMES = {
        '0/0': '0/0',
        '∞/∞': '\\infty/\\infty',
        '0·∞': '0 \\cdot \\infty',
        '∞-∞': '\\infty - \\infty',
        '0^0': '0^{0}',
        '∞^0': '\\infty^{0}',
        '1^∞': '1^{\\infty}',
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
            expr = sympify(s, locals=local_dict)
            return expr
        except Exception as e:
            raise ValueError(f"Error al parsear la expresión: {e}")

    def _parse_point(self, s):
        s = s.strip().lower().replace(' ', '')
        mapping = {
            'oo': oo, 'inf': oo, '∞': oo, 'infinito': oo, '+oo': oo, '+inf': oo, '+∞': oo,
            '-oo': -oo, '-inf': -oo, '-∞': -oo, '-infinito': -oo,
            'pi': pi, 'π': pi,
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
        sub_latex = latex_str.replace(var, wrapped)
        if sub_latex == latex_str:
            return None
        return sub_latex

    def _paso1_indet_tex(self, expr, form_tex):
        """Build paso 1 tex showing the limit, substitution, and indeterminate form."""
        limit_tex = self._limit_tex(expr)
        sub_tex = self._substitution_tex(expr)
        if sub_tex:
            return f'{limit_tex} = {sub_tex} \\text{{ es una indeterminación }} \\boxed{{{form_tex}}}'
        return f'{limit_tex} \\text{{ es una indeterminación }} \\boxed{{{form_tex}}}'

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
            val = expr.subs(self.var, point)
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
            return 'logarítmico'
        if has_log:
            return 'logarítmico'
        if has_trig:
            return 'trigonométrico'
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
                    return '∞-∞'

        frac = together(expr)
        num, den = fraction(frac)
        num_val = self._safe_sub(num)
        den_val = self._safe_sub(den)
        num_zero = self._is_zero(num_val)
        den_zero = self._is_zero(den_val)
        num_inf = self._is_inf(num_val)
        den_inf = self._is_inf(den_val)

        if num_zero and den_zero:
            return '0/0'
        if num_inf and den_inf:
            return '∞/∞'

        if expr.func == Pow:
            base, exp = expr.args
            base_val = self._safe_sub(base)
            exp_val = self._safe_sub(exp)
            if self._is_zero(base_val) and self._is_zero(exp_val):
                return '0^0'
            if self._is_inf(base_val) and self._is_zero(exp_val):
                return '∞^0'
            if base_val == 1 and self._is_inf(exp_val):
                return '1^∞'

        if expr.func == Mul:
            args_zero = any(self._is_zero(self._safe_sub(a)) for a in expr.args)
            args_inf = any(self._is_inf(self._safe_sub(a)) for a in expr.args)
            if args_zero and args_inf:
                return '0·∞'

        if self._is_indeterminate(num_val) or self._is_indeterminate(den_val):
            return None
        return None

    def solve(self):
        try:
            self._limit_type = self._classify_expr(self.expr)
            form = self._detect_form()

            # 0^0 is indeterminate but SymPy evaluates 0**0 = 1
            force_indeterminate = False
            if self.expr.func == Pow:
                b, e = self.expr.args
                if self._is_zero(self._safe_sub(b)) and self._is_zero(self._safe_sub(e)):
                    force_indeterminate = True

            if force_indeterminate:
                direct_val = nan
            else:
                direct_val = self._safe_sub(self.expr)

            if not self._is_indeterminate(direct_val):
                self._add_step(
                    'Sustitución directa',
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
            if form in ('0/0', '∞/∞', '∞-∞', '1^∞', '0^0', '∞^0'):
                if form == '0/0':
                    result = self._solve_0_over_0_detailed()
                elif form == '∞/∞':
                    result = self._solve_inf_over_inf_detailed()
                elif form == '∞-∞':
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
                    'Expresión original',
                    f'{self._limit_tex(self.expr)}',
                    f'Vamos a calcular el límite indicado.',
                    'expression'
                )
                form_tex = self.FORM_NAMES.get(form, form or 'desconocida')
                if form:
                    self._add_step(
                        'Indeterminación detectada',
                        f'{self._limit_tex(self.expr)} \\text{{ es una indeterminación }} \\boxed{{{form_tex}}}',
                        f'Al sustituir directamente obtenemos {form}. Aplicaremos técnicas para resolverla.',
                        'warning'
                    )
                else:
                    self._add_step(
                        'Forma indeterminada',
                        f'\\text{{La expresión presenta una indeterminación}}',
                        'La expresión es indeterminada. Usaremos técnicas generales.',
                        'warning'
                    )
                if form == '0/0':
                    result = self._solve_0_over_0()
                elif form == '∞/∞':
                    result = self._solve_inf_over_inf()
                elif form == '0·∞':
                    result = self._solve_0_times_inf()
                elif form == '∞-∞':
                    result = self._solve_inf_minus_inf()
                elif form in ('1^∞', '0^0', '∞^0'):
                    result = self._solve_exponential(form)
                else:
                    result = self._solve_fallback()

                if result is not None and not self._is_indeterminate(result):
                    self._add_step(
                        'Resultado final',
                        f'\\boxed{{{self._limit_tex(self.expr)} = {self._latex(result)}}}',
                        f'El límite es {self._latex(result)}.',
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
                'Cálculo simbólico (SymPy)',
                f'{self._latex(expr)} \\to {self._latex(result)}',
                'Utilizamos el motor de cálculo simbólico para obtener el resultado.',
                'success'
            )
            return result
        except Exception as e:
            self._add_step(
                'Error',
                '',
                f'No se pudo calcular el límite: {str(e)}',
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
            new_den = sp.expand(den * conj)
        else:
            new_num = sp.expand(num * conj)
            new_den = sp.expand(den * conj)
        new_expr = sp.cancel(new_num / new_den)
        val = self._safe_sub(new_expr)
        if self._is_indeterminate(val):
            return None
        return (new_expr, val, {'target': target, 'conj': conj, 'is_num': is_num})

    def _solve_trigonometric_0_over_0(self, expr=None):
        if expr is None:
            expr = self.expr
        self.steps = []
        x, point = self.var, self.point

        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '0/0'),
            'Se sustituye la tendencia de x para hallar la indeterminación.',
            'warning'
        )

        special_limits = (
            '\\lim_{u \\to 0} \\frac{\\sin u}{u} = 1 \\\\'
            '\\lim_{u \\to 0} \\frac{u}{\\sin u} = 1 \\\\'
            '\\lim_{u \\to 0} \\frac{1 - \\cos u}{u} = 0'
        )
        self._add_step(
            'Paso 2',
            f'\\text{{Aplicamos límites trigonométricos especiales:}} \\\\{special_limits}',
            'Se utilizan límites trigonométricos fundamentales.',
            'info'
        )

        # Use silent solving to avoid showing L'Hôpital steps
        val = self._solve_silent(expr)
        if val is not None and not self._is_indeterminate(val):
            result_tex = self._latex(val)
            paso3_tex = f'\\boxed{{{self._limit_tex(expr)} = {result_tex}}}'
            self._add_step(
                'Paso 3',
                paso3_tex,
                'Se halla el límite.',
                'info'
            )
            return val

        return self._solve_fallback(expr)

    def _solve_logarithmic_0_over_0(self, expr=None):
        if expr is None:
            expr = self.expr
        self.steps = []
        x, point = self.var, self.point

        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '0/0'),
            'Se sustituye la tendencia de x para hallar la indeterminación.',
            'warning'
        )

        log_limit_tex = '\\lim_{u \\to 0} \\frac{e^{u} - 1}{u} = 1'
        self._add_step(
            'Paso 2',
            f'\\text{{Aplicamos el límite especial: }} {log_limit_tex}',
            'Se utiliza el límite logarítmico fundamental.',
            'info'
        )

        # Use silent solving (no sub-steps visible)
        sympy_limit = self._solve_silent(expr)
        if sympy_limit is not None and not self._is_indeterminate(sympy_limit):
            result_tex = self._latex(sympy_limit)
            paso3_tex = f'\\boxed{{{self._limit_tex(expr)} = {result_tex}}}'
            self._add_step(
                'Paso 3',
                paso3_tex,
                'Se halla el límite.',
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
        if self._limit_type == 'trigonométrico':
            return self._solve_trigonometric_0_over_0(expr)
        if self._limit_type == 'logarítmico':
            return self._solve_logarithmic_0_over_0(expr)

        # Default: rational / irrational path
        self._add_step(
            'Paso 1',
            self._paso1_indet_tex(expr, '0/0'),
            'Se sustituye la tendencia de x para hallar la indeterminación.',
            'warning'
        )

        frac = together(expr)
        num, den = fraction(frac)
        is_irracional = self._limit_type == 'algebraico irracional'

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
            self._add_step('Paso 3', step3_tex, 'Se sustituye el valor de la tendencia de x para hallar el límite.', 'info')
            return val

        if result_type == 'rationalize' and rat_info is not None:
            what = 'numerador' if rat_info['is_num'] else 'denominador'
            expr_tex = self._latex(expr)
            if isinstance(expr, sp.Add):
                expr_tex = f'\\left({expr_tex}\\right)'
            conj_tex = self._latex(rat_info['conj'])
            new_tex = self._latex(simplified)
            step2_tex = f"{expr_tex} \\cdot \\frac{{{conj_tex}}}{{{conj_tex}}} = {new_tex}"
            self._add_step('Paso 2', step2_tex, f'Se racionaliza el {what} para eliminar la indeterminación.', 'info')

            sub_tex = self._substitution_tex(simplified)
            if sub_tex:
                step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {new_tex} = {sub_tex} = {self._latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}"
            else:
                step3_tex = f"\\lim_{{{x.name} \\to {self._point_tex()}}} {new_tex} = {self._latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}"
            self._add_step('Paso 3', step3_tex, 'Se sustituye el valor de la tendencia de x para hallar el límite.', 'info')
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

    def _try_factor(self, num, den):
        x, point = self.var, self.point
        num_f = factor(num)
        den_f = factor(den)
        if num_f != num or den_f != den:
            orig = sp.simplify(num / den)
            factored = sp.simplify(num_f / den_f)
            which = 'numerador' if num_f != num else 'denominador' if den_f != den else 'ambos'
            self._add_step(
                'Factorización',
                f'\\frac{{{self._latex(num)}}}{{{self._latex(den)}}} = \\frac{{{self._latex(num_f)}}}{{{self._latex(den_f)}}}',
                f'Se factoriza {which} para eliminar la indeterminación.',
                'info'
            )
            simplified = cancel(num_f / den_f)
            if simplified != factored:
                self._add_step(
                    'Cancelación',
                    f'\\frac{{{self._latex(num_f)}}}{{{self._latex(den_f)}}} = {self._latex(simplified)}',
                    'Cancelamos los factores comunes.',
                    'info'
                )
            val = self._safe_sub(simplified)
            if not self._is_indeterminate(val):
                self._add_step(
                    'Evaluación',
                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(simplified)} = {self._latex(val)}',
                    f'Se sustituye el valor de la tendencia de {x.name} para hallar el límite.',
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
            new_den = sp.expand(den * conj)
        else:
            new_num = sp.expand(num * conj)
            new_den = sp.expand(den * conj)
        what = 'numerador' if is_num else 'denominador'
        self._add_step(
            'Racionalización',
            f'{self._latex(expr)} \\cdot \\frac{{{self._latex(conj)}}}{{{self._latex(conj)}}}',
            f'Se racionaliza el {what} para eliminar la indeterminación.',
            'info'
        )
        new_expr = sp.cancel(new_num / new_den)
        self._add_step(
            'Simplificación',
            f'{self._latex(new_expr)}',
            'Simplificamos la expresión resultante.',
            'info'
        )
        val = self._safe_sub(new_expr)
        if not self._is_indeterminate(val):
            self._add_step(
                'Evaluación',
                f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {self._latex(val)}',
                f'Se sustituye el valor de la tendencia de {x.name} para hallar el límite.',
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
            lbl = labels.get(i + 1, f'{i+1}ª')
            self._add_step(
                f'L\'Hôpital ({lbl} aplicación)',
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
                'L\'Hôpital',
                f'\\text{{Se alcanzó el máximo de iteraciones ({max_iter}).}}',
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
            'Se sustituye la tendencia de x para hallar la indeterminación.',
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
                f'Se divide la expresión entre {highest_tex} (la mayor potencia de {x.name}).',
                'info'
            )

            if not self._is_indeterminate(val):
                substituted_after_tex = self._substitute_point_tex(new_expr)
                self._add_step(
                    'Paso 3',
                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {substituted_after_tex} = {self._latex(val)} \\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}',
f'Sustituimos {x.name} = {self._point_tex()} en la expresión simplificada para obtener el valor final.',
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
                'División por máxima potencia',
                f'\\frac{{{self._latex(num)}}}{{{self._latex(den)}}} = \\frac{{{self._latex(new_num)}}}{{{self._latex(new_den)}}}',
                f'Dividimos numerador y denominador por {self._latex(xh)}, la máxima potencia de {x.name}.',
                'info'
            )
            if not self._is_indeterminate(val):
                substituted_after = new_expr.subs(x, self.point)
                substituted_after_tex = self._latex(substituted_after)
                self._add_step(
                    'Evaluación',
                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {substituted_after_tex} = {self._latex(val)}',
                    f'Sustituimos {x.name} = {self._point_tex()} en la expresión simplificada.',
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
            new_expr = sp.simplify(zero_factor / (1 / inf_factor))
            self._add_step(
                'Transformación a 0/0',
                f'{self._latex(expr)} = \\frac{{{self._latex(zero_factor)}}}{{\\frac{{1}}{{{self._latex(inf_factor)}}}}} = {self._latex(new_expr)}',
                'Reescribimos como cociente para aplicar las técnicas de 0/0.',
                'info'
            )
            tf = together(new_expr)
            nn, dd = fraction(tf)
            sub = self._solve_0_over_0_sub(nn, dd)
            if sub is not None:
                return sub
            lh = self._try_lhopital(new_expr)
            if lh is not None:
                return lh
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
            'Se sustituye la tendencia de x para hallar la indeterminación.',
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
                self._add_step(
                    'Paso 3',
                    f'\\lim_{{{x.name} \\to {self._point_tex()}}} {self._latex(new_expr)} = {self._latex(val)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}',
                    'Se sustituye el valor de la tendencia de x para hallar el límite.',
                    'info'
                )
                return val
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
                        'Se sustituye el valor de la tendencia de x para hallar el límite.',
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
                            'Se sustituye el valor de la tendencia de x para hallar el límite.',
                            'info'
                        )
                        return sub_val
                    lh = self._try_lhopital(frac)
                    if lh is not None:
                        return lh
                elif form == '∞/∞':
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
                                'Se sustituye el valor de la tendencia de x para hallar el límite.',
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
                'Combinación de términos',
                f'{self._latex(expr)} = {self._latex(frac)}',
                'Combinamos los términos en una sola fracción.',
                'info'
            )
            val = self._safe_sub(frac)
            if not self._is_indeterminate(val):
                return val
            form = self._detect_form(frac)
            if form == '0/0':
                n, d = fraction(frac)
                return self._solve_0_over_0_sub(n, d)
            if form == '∞/∞':
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
        elif form == '∞/∞':
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
            'Se sustituye la tendencia de x para hallar la indeterminación.',
            'warning'
        )

        if expr.func != Pow:
            return self._solve_fallback(expr)

        base, exponent = expr.args
        f_tex = self._latex(base)
        g_tex = self._latex(exponent)

        f_minus_1 = sp.simplify(base - 1)
        new_power = sp.simplify(f_minus_1 * exponent)
        new_power_tex = self._latex(new_power)

        paso2_tex = (
            f'\\text{{Aplicamos la igualdad: }} '
            f'\\lim \\left({f_tex}\\right)^{{{g_tex}}} = e^{{\\lim ({f_tex}-1) \\cdot {g_tex}}} \\\\'
            f'({f_tex}-1) \\cdot {g_tex} = ({self._latex(f_minus_1)}) \\cdot {g_tex} = {new_power_tex}'
        )
        self._add_step(
            'Paso 2',
            paso2_tex,
            'Se aplica la igualdad fundamental de límites exponenciales.',
            'info'
        )

        val = self._safe_sub(new_power)
        if not self._is_indeterminate(val):
            result = sp.exp(val)
            paso3_tex = (
                f'\\lim \\left({f_tex}\\right)^{{{g_tex}}} = e^{{{new_power_tex}}} = {self._latex(result)} \\\\'
                f'\\boxed{{{self._limit_tex(expr)} = {self._latex(result)}}}'
            )
            self._add_step(
                'Paso 3',
                paso3_tex,
                'Se halla el límite.',
                'info'
            )
            return result

        ln_expr = sp.simplify(exponent * log(base))
        self._add_step(
            'Paso 2 (alt)',
            f'\\text{{Sea }} L = {orig_tex} \\\\ \\ln L = {g_tex} \\cdot \\ln\\left({f_tex}\\right) = {self._latex(ln_expr)}',
            'Se aplica logaritmo natural para transformar la exponencial.',
            'info'
        )
        ln_val = self._safe_sub(ln_expr)
        if not self._is_indeterminate(ln_val):
            result_ln = ln_val
        else:
            result_ln = self._solve_silent(ln_expr)
        if result_ln is not None and not self._is_indeterminate(result_ln):
            L = exp(result_ln)
            self._add_step(
                'Paso 3',
                f'\\ln L = {self._latex(result_ln)} \\implies L = e^{{{self._latex(result_ln)}}} = {self._latex(L)} \\\\ \\boxed{{{self._limit_tex(expr)} = {self._latex(L)}}}',
                'Se aplica exponencial para hallar el límite.',
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
            'Transformación logarítmica',
            f'\\text{{Sea }} L = {self._latex(expr)} \\\\ \\ln L = {self._latex(exponent)} \\cdot \\ln\\left({self._latex(base)}\\right) = {self._latex(ln_expr)}',
            'Aplicamos logaritmo natural para convertir la exponencial en un producto.',
            'info'
        )
        ln_val = self._safe_sub(ln_expr)
        if not self._is_indeterminate(ln_val):
            L = exp(ln_val)
            self._add_step(
                'Exponenciación',
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
        elif form_ln == '∞/∞':
            result_ln = self._solve_inf_over_inf(ln_expr)
        elif form_ln == '0·∞':
            result_ln = self._solve_0_times_inf(ln_expr)
        else:
            lh = self._try_lhopital(ln_expr)
            if lh is not None:
                result_ln = lh
        if result_ln is not None and not self._is_indeterminate(result_ln):
            L = exp(result_ln)
            self._add_step(
                'Exponenciación',
                f'\\ln L = {self._latex(result_ln)} \\implies L = e^{{{self._latex(result_ln)}}} = {self._latex(L)}',
                'Aplicamos exponencial para despejar L.',
                'info'
            )
            return L
        return self._solve_fallback(expr)
