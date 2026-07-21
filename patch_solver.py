from pathlib import Path

path = Path('solver.py')
text = path.read_text(encoding='utf-8')
start = text.find('substituted_after = new_expr.subs(x, self.point)')
end = text.find("f'Sustituimos {x.name} = {self._point_tex()} en la expresión simplificada para obtener el valor final.'", start)
new_chunk = """substituted_after = new_expr.subs(x, self.point)
                substituted_after_tex = self._latex(substituted_after)
                self._add_step(
                    'Paso 3',
                    f'\\\\lim_{{{x.name} \\\\to {self._point_tex()}}} {self._latex(new_expr)} = {substituted_after_tex} = {self._latex(val)} \\\\\\ \\\\boxed{{{self._limit_tex(expr)} = {self._latex(val)}}}',
"""
text = text[:start] + new_chunk + text[end:]
path.write_text(text, encoding='utf-8')
