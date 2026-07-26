import re
import sympy as sp
from flask import Flask, render_template, request, jsonify
from solver import LimitSolver, expr_to_latex

app = Flask(__name__)

@app.after_request
def set_charset(response):
    if response.content_type and 'text/html' in response.content_type and 'charset' not in response.content_type:
        response.content_type = 'text/html; charset=utf-8'
    return response



_LOCAL_DICT_CACHE = {}

def _get_local_dict(var_str):
    if var_str not in _LOCAL_DICT_CACHE:
        var = sp.Symbol(var_str, real=True)
        _LOCAL_DICT_CACHE[var_str] = {
            var_str: var,
            'ln': sp.log, 'log': sp.log,
            'sen': sp.sin, 'sin': sp.sin, 'cos': sp.cos,
            'tan': sp.tan, 'tg': sp.tan,
            'cot': sp.cot, 'cotg': sp.cot,
            'sec': sp.sec, 'csc': sp.csc,
            'arcsen': sp.asin, 'arccos': sp.acos, 'arctg': sp.atan,
            'sqrt': sp.sqrt, 'exp': sp.exp,
        }
    return _LOCAL_DICT_CACHE[var_str]


def _point_to_tex(pt):
    pt = pt.strip().replace(' ', '')
    mapping = {
        'oo': '\\infty', 'inf': '\\infty', '∞': '\\infty',
        '-oo': '-\\infty', '-inf': '-\\infty', '-∞': '-\\infty',
        '+oo': '\\infty', '+inf': '\\infty', '+∞': '\\infty',
        'pi': '\\pi', 'π': '\\pi',
    }
    return mapping.get(pt, pt)


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


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    expr_input = ''
    expr_latex = ''
    variable = 'x'
    point = '0'

    if request.method == 'POST':
        expr_input = request.form.get('expression', '').strip()
        variable = request.form.get('variable', 'x').strip() or 'x'
        point = request.form.get('point', '0').strip() or '0'

        if not expr_input:
            result = {
                'steps': [],
                'result_tex': None,
                'form': None,
                'error': 'Por favor, ingresa una expresión.',
            }
        else:
            try:
                solver = LimitSolver(
                    expr_input,
                    var_str=variable,
                    point_str=point,
                )
                result = solver.solve()
                if '\\' in expr_input:
                    expr_latex = expr_input
                else:
                    expr_latex = sp.latex(solver.expr)
            except Exception as e:
                result = {
                    'steps': [],
                    'result_tex': None,
                    'form': None,
                    'error': str(e),
                }

    return render_template(
        'index.html',
        result=result,
        expr=expr_input,
        expr_latex=expr_latex,
        variable=variable,
        point=point,
    )


@app.route('/preview_limit', methods=['POST'])
def preview_limit():
    expr_str = request.form.get('expression', '').strip()
    var_str = request.form.get('variable', 'x').strip() or 'x'
    point_str = request.form.get('point', '0').strip() or '0'

    if not expr_str:
        return jsonify({'limit_tex': None, 'error': 'Expresión vacía'})

    try:
        if '\\' in expr_str:
            from sympy.parsing.latex import parse_latex
            parse_latex(expr_str)
            pt_tex = _point_to_tex(point_str)
            limit_tex = f'\\lim_{{{var_str} \\to {pt_tex}}} {expr_str}'
            return jsonify({'limit_tex': limit_tex, 'error': None})
        else:
            expr_sympy = _normalize_expression(expr_str).replace('^', '**')
            local_dict = _get_local_dict(var_str).copy()
            local_dict['e'] = sp.E
            expr = sp.sympify(expr_sympy, locals=local_dict, evaluate=False)
            expr_tex = expr_to_latex(expr)
            pt_tex = _point_to_tex(point_str)
            limit_tex = f'\\lim_{{{var_str} \\to {pt_tex}}} {expr_tex}'
            return jsonify({'limit_tex': limit_tex, 'error': None})
    except Exception as e:
        return jsonify({'limit_tex': None, 'error': str(e)})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)



