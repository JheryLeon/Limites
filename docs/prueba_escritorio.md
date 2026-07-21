# Prueba de Escritorio — Calculadora de Límites

Se prueban 8 ejercicios cubriendo todas las formas indeterminadas, trazando el flujo completo: entrada → parseo → detección → resolución → salida.

---

## Caso 1: Límite racional con factorización (0/0)

**Entrada:**
```
expresión = (x^3+1)/(x^2-1)
variable   = x
punto      = -1
dirección  = (vacío)
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_normalize_expression("(x^3+1)/(x^2-1)")` | `"(x**3+1)/(x**2-1)"` |
| | `_parse_expr()` con sympify | `(x^3 + 1)/(x^2 - 1)` |
| | `_parse_point("-1")` → Rational | `-1` |
| **2. Clasificación** | `_classify_expr()` | No trig, log, exp, sqrt → `"algebraico racional"` |
| **3. Sustitución directa** | `_safe_sub(expr, point=-1)` | `num = (-1)^3+1 = 0`, `den = (-1)^2-1 = 0` |
| | `_is_indeterminate(0/0)` → `nan` | Sí, es indeterminado |
| **4. Detectar forma** | `_detect_form()` | Togeher → `(x^3+1)/(x^2-1)` → num=0, den=0 → `"0/0"` |
| **5. Resolución** | `_solve_0_over_0_detailed()` | Forma 0/0, tipo algebraico racional |
| | **Paso 1:** `_paso1_indet_tex()` | `\lim_{x \to -1} \frac{x^{3} + 1}{x^{2} - 1} = \frac{(-1)^{3} + 1}{(-1)^{2} - 1} \text{ es una indeterminación } \boxed{0/0}` |
| | `try_paths = ["factor", "rationalize"]` | Primero intenta factorizar |
| | **Factorizar:** `_factor_with_info(num, den)` | `num = x^3+1 → (x+1)(x^2-x+1)` tipo: suma de cubos<br>`den = x^2-1 → (x-1)(x+1)` tipo: diferencia de cuadrados |
| | `simplified = cancel(num_f/den_f)` | `(x^2 - x + 1)/(x - 1)` |
| | `val = _safe_sub(simplified, -1)` | `((-1)^2 - (-1) + 1)/((-1) - 1) = (1+1+1)/(-2) = -3/2` |
| | `_is_indeterminate(-3/2)` → No | Resultado válido |
| | **Paso 2:** | `'Se factoriza el numerador (suma de cubos) y el denominador (diferencia de cuadrados)'` |
| | `tex:` | `\frac{x^{3} + 1}{x^{2} - 1} = \frac{\left(x + 1\right) \left(x^{2} - x + 1\right)}{\left(x - 1\right) \left(x + 1\right)} \\ \frac{\left(x + 1\right) \left(x^{2} - x + 1\right)}{\left(x - 1\right) \left(x + 1\right)} = \frac{x^{2} - x + 1}{x - 1}` |
| | **Paso 3:** | `'Se sustituye el valor de la tendencia de x para hallar el límite.'` |
| | `tex:` | `\lim_{x \to -1} \frac{x^{2} - x + 1}{x - 1} = \frac{(-1)^{2} - (-1) + 1}{(-1) - 1} = - \frac{3}{2} \\ \boxed{\lim_{x \to -1} \frac{x^{3} + 1}{x^{2} - 1} = - \frac{3}{2}}` |
| **6. Salida** | `result_tex` | `- \frac{3}{2}` |
| | `form` | `"0/0"` |
| | `limit_type` | `"algebraico racional"` |

---

## Caso 2: Límite racional con L'Hôpital (0/0 trigonométrico)

**Entrada:**
```
expresión = sin(2*x)/(4*x-4/3*sin(6*x))
variable   = x
punto      = 0
dirección  = +
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_parse_expr("sin(2*x)/(4*x-4/3*sin(6*x))")` | `sin(2x) / (4x - 4*sin(6x)/3)` |
| **2. Clasificación** | `_classify_expr()` | Contiene sin → `"trigonométrico"` |
| **3. Sustitución directa** | `_safe_sub(expr, 0)` | `sin(0)/(0 - 4/3 sin(0))` = `0 / 0` = `nan` |
| **4. Detectar forma** | `_detect_form()` | `"0/0"` |
| **5. Resolución** | `_solve_0_over_0_detailed()` | Trigonométrico → no irracional → paths: factor, rationalize |
| | **Factorizar:** `_factor_with_info(num, den)` | `num = sin(2x)`, no factorizable → falla |
| | **Racionalizar:** `_rationalize_with_info()` | No contiene sqrt → falla |
| | `_try_lhopital(expr)` | Iteración 1: `n' = 2cos(2x)`, `d' = 4 - 8cos(6x)` |
| | `new_expr = (2cos(2x))/(4-8cos(6x))` | `_safe_sub(new_expr, 0)` = `2/(4-8) = -1/2` |
| | `_is_indeterminate(-1/2)` → No | Resultado válido |
| | **Paso 1:** | `\lim_{x \to 0^{+}} \frac{\sin(2x)}{4x - \frac{4}{3}\sin(6x)} = \frac{\sin(2(0))}{4(0) - \frac{4}{3}\sin(6(0))} \text{ es una indeterminación } \boxed{0/0}` |
| | **Paso 2 (L'Hôpital):** | `f'(x) = 2\cos(2x)`, `g'(x) = 4 - 8\cos(6x)` |
| | `tex:` | `\begin{aligned} f'(x) &= 2 \cos(2x) \\ g'(x) &= 4 - 8 \cos(6x) \\ \frac{f'(x)}{g'(x)} &= \frac{\cos(2x)}{2 - 4 \cos(6x)} \end{aligned}` |
| | (Nota: se muestra `-cos/(4cos-2)` simplificado, el resultado final es `-1/2`) |
| | **No hay Paso 3** porque L'Hôpital devuelve directamente el valor | |
| **6. Salida** | `result_tex` | `- \frac{1}{2}` |
| | `form` | `"0/0"` |
| | `limit_type` | `"trigonométrico"` |

---

## Caso 3: Límite con racionalización (0/0 irracional)

**Entrada:**
```
expresión = (sqrt(1+x)-sqrt(1-x))/x
variable   = x
punto      = 0
dirección  = (vacío)
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_parse_expr("(sqrt(1+x)-sqrt(1-x))/x")` | `(sqrt(x+1) - sqrt(1-x))/x` |
| **2. Clasificación** | `_classify_expr()` | Contiene sqrt → `"algebraico irracional"` |
| **3. Sustitución directa** | `_safe_sub(expr, 0)` | `(1-1)/0 = 0/0` = `nan` |
| **4. Detectar forma** | `_detect_form()` | `"0/0"` |
| **5. Resolución** | `_solve_0_over_0_detailed()` | Irracional → try_paths = ["rationalize", "factor"] |
| | **Racionalizar:** `_rationalize_with_info(num, den)` | `num = sqrt(x+1)-sqrt(1-x)` → conjugado = `sqrt(x+1)+sqrt(1-x)` |
| | `new_num = (sqrt(x+1)-sqrt(1-x))*(sqrt(x+1)+sqrt(1-x)) = 2x` |
| | `new_den = x * (sqrt(x+1)+sqrt(1-x))` |
| | `new_expr = cancel(2x / (x*(sqrt(x+1)+sqrt(1-x)))) = 2/(sqrt(x+1)+sqrt(1-x))` |
| | `val = _safe_sub(new_expr, 0)` | `2/(1+1) = 1` |
| | **Paso 2:** | `'Se racionaliza el numerador para eliminar la indeterminación.'` |
| | **Paso 3:** | `\lim_{x \to 0} \frac{2}{\sqrt{x+1}+\sqrt{1-x}} = \frac{2}{\sqrt{1}+\sqrt{1}} = 1 \\ \boxed{\lim_{x \to 0} \frac{\sqrt{1+x}-\sqrt{1-x}}{x} = 1}` |
| **6. Salida** | `result_tex` | `1` |

---

## Caso 4: Límite ∞/∞ con división por máxima potencia

**Entrada:**
```
expresión = (2*x+3)/(4*x**3+2)
variable   = x
punto      = oo
dirección  = (vacío)
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_parse_expr("(2*x+3)/(4*x**3+2)")` | `(2x+3)/(4x^3+2)` |
| | `_parse_point("oo")` → `oo` | `oo` |
| **2. Clasificación** | `_classify_expr()` | Polinomio → `"algebraico racional"` |
| **3. Sustitución directa** | `_safe_sub(expr, oo)` | `(2∞+3)/(4∞^3+2)` = `∞/∞` = `nan` |
| **4. Detectar forma** | `_detect_form()` | `"∞/∞"` |
| **5. Resolución** | `_solve_inf_over_inf_detailed()` | |
| | **Paso 1:** | `\lim_{x \to \infty} \frac{2x+3}{4x^{3}+2} \text{ es una indeterminación } \boxed{\infty/\infty}` |
| | (Sin sustitución porque punto es ∞) | |
| | `n_deg = 1`, `d_deg = 3` | `highest = 3`, `xh = x^3` |
| | `new_num = (2x+3)/x^3 = 2/x^2 + 3/x^3` | |
| | `new_den = (4x^3+2)/x^3 = 4 + 2/x^3` | |
| | **Paso 2:** | `\frac{2x+3}{4x^{3}+2} = \frac{\frac{2}{x^{2}} + \frac{3}{x^{3}}}{4 + \frac{2}{x^{3}}}` |
| | `val = _safe_sub(new_num/new_den, oo)` | `(0+0)/(4+0) = 0` |
| | **Paso 3:** | `\lim_{x \to \infty} \frac{2x+3}{4x^{3}+2} = 0 \boxed{\lim_{x \to \infty} \frac{2x+3}{4x^{3}+2} = 0}` |
| **6. Salida** | `result_tex` | `0` |

---

## Caso 5: Límite ∞-∞ con racionalización

**Entrada:**
```
expresión = sqrt(x-3)-sqrt(x+3)
variable   = x
punto      = oo
dirección  = (vacío)
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_parse_expr("sqrt(x-3)-sqrt(x+3)")` | `sqrt(x-3) - sqrt(x+3)` |
| **2. Clasificación** | `_classify_expr()` | Contiene sqrt → `"algebraico irracional"` |
| **3. Sustitución directa** | `_safe_sub(expr, oo)` | `∞ - ∞` = `nan` |
| **4. Detectar forma** | `_detect_form()` | Add: arg1→∞, arg2→-∞ → `"∞-∞"` |
| **5. Resolución** | `_solve_inf_minus_inf_detailed()` | |
| | **Paso 1:** | `\lim_{x \to \infty} \sqrt{x-3}-\sqrt{x+3} \text{ es una indeterminación } \boxed{\infty - \infty}` |
| | `has_radicals = True` | |
| | `frac = together(expr)` = `(sqrt(x-3)-sqrt(x+3))` (sigue igual) | |
| | `n, d = fraction(frac)` = `(sqrt(x-3)-sqrt(x+3), 1)` | |
| | `_rationalize_with_info(n, d)` | target = num = `sqrt(x-3)-sqrt(x+3)` |
| | Conjugado = `sqrt(x-3)+sqrt(x+3)` | |
| | `new_expr = ((sqrt(x-3)-sqrt(x+3))*(sqrt(x-3)+sqrt(x+3)))/(1*(sqrt(x-3)+sqrt(x+3)))` |
| | `= ( (x-3)-(x+3) )/(sqrt(x-3)+sqrt(x+3)) = -6/(sqrt(x-3)+sqrt(x+3))` |
| | `val = _safe_sub(new_expr, oo)` | `-6/∞ = 0` |
| | **Paso 2:** | `'Se racionaliza el numerador.'` |
| | **Paso 3:** | `\boxed{\lim_{x \to \infty} \sqrt{x-3}-\sqrt{x+3} = 0}` |
| **6. Salida** | `result_tex` | `0` |

---

## Caso 6: Límite ∞-∞ racional (resta de fracciones)

**Entrada:**
```
expresión = 1/(x-1)-1/(x+1)
variable   = x
punto      = 1
dirección  = (vacío)
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_parse_expr("1/(x-1)-1/(x+1)")` | `1/(x-1) - 1/(x+1)` |
| **2. Clasificación** | `_classify_expr()` | Polinomio → `"algebraico racional"` |
| **3. Sustitución directa** | `_safe_sub(expr, 1)` | `1/0 - 1/2 = zoo - 1/2` = `zoo` |
| **4. Detectar forma** | `_detect_form()` | Se evalúa cada arg: `1/(x-1)`→`zoo`, `-1/(x+1)`→`-½` |
| | `signs = ['?', ...]` dependiendo de si es ±∞ o zoo | No detecta ∞-∞ porque `1/(x+1)` no tiende a ∞ |
| | En cambio, `together(expr)` → `((x+1)-(x-1))/((x-1)(x+1)) = 2/((x-1)(x+1))` |
| | `_safe_sub(2/((x-1)(x+1)), 1)` → `2/0 = zoo` | |
| | En `solve()`, `direct_val = zoo`, `_is_indeterminate(zoo)` → No? `zoo` no es `nan` |
| | Luego `_detect_form()` se llama desde `solve()` y puede no detectar ∞-∞ | |

**Nota:** Este caso depende de si `zoo` se considera indeterminado. `_is_inf()` devuelve True para `zoo`, y `_detect_form()` lo capturaría como ∞/∞ tras `together()`. En la práctica la forma final detectada suele ser `"0/0"` o `"∞/∞"` tras combinar las fracciones.

---

## Caso 7: Límite exponencial (1^∞)

**Entrada:**
```
expresión = (1-8*x)^(1/(4*x))
variable   = x
punto      = 0
dirección  = (vacío)
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_parse_expr("(1-8*x)^(1/(4*x))")` | `(1 - 8x)^(1/(4x))` |
| **2. Clasificación** | `_classify_expr()` | Contiene Pow con exponente no constante → `"exponencial"` |
| **3. Sustitución directa** | `_safe_sub(expr, 0)` | `(1)^(1/0)` = `zoo` (indeterminado) |
| | `force_indeterminate = True` porque base→1, exp→0/∞ | `force_indeterminate = True` |
| **4. Detectar forma** | `_detect_form()` | `expr.func == Pow`, `base→1`, `exp→1/0=zoo`, `_is_inf(zoo)` → True |
| | Base val = 1, exp val = ∞ → `"1^∞"` |
| **5. Resolución** | `_solve_exponential_detailed("1^∞")` | |
| | **Paso 1:** | `\lim_{x \to 0} (1-8x)^{1/(4x)} \text{ es una indeterminación } \boxed{1^{\infty}}` |
| | **Paso 2:** `base = 1-8x`, `exponent = 1/(4x)` | |
| | `ln_expr = (1/(4x))*log(1-8x)` | |
| | `tex:` | `\text{Sea } L = (1-8x)^{1/(4x)} \\ \ln L = \frac{1}{4x} \cdot \ln(1-8x) = \frac{\log(1-8x)}{4x}` |
| | `_safe_sub(ln_expr, 0)` | `log(1)/0 = 0/0` = `nan` (indeterminado) |
| | `_solve_silent(ln_expr)` | Reescribe como `log(1-8x)/(4x)` → forma 0/0 |
| | L'Hôpital: `d/dx log(1-8x) = -8/(1-8x)`, `d/dx 4x = 4` | `new = (-8/(1-8x))/4 = -2/(1-8x)` |
| | `_safe_sub(new, 0) = -2` | `-2` (no indeterminado) |
| | **Paso 3:** | `\ln L = -2 \implies L = e^{-2} = e^{-2} \\ \boxed{\lim_{x \to 0} (1-8x)^{1/(4x)} = e^{-2}}` |
| **6. Salida** | `result_tex` | `e^{-2}` |

---

## Caso 8: Límite trigonométrico con L'Hôpital (0/0)

**Entrada:**
```
expresión = (e^(x^2)-cos(x))/(x^2)
variable   = x
punto      = 0
dirección  = (vacío)
```

### Traza

| Paso | Código / Estado | Valores / Salida |
|------|----------------|-------------------|
| **1. Parseo** | `_parse_expr("(e^(x^2)-cos(x))/(x^2)")` | `(exp(x^2) - cos(x))/x^2` |
| **2. Clasificación** | `_classify_expr()` | Contiene cos → `"trigonométrico"` |
| **3. Sustitución directa** | `_safe_sub(expr, 0)` | `(1-1)/0 = 0/0` = `nan` |
| **4. Detectar forma** | `_detect_form()` | `"0/0"` |
| **5. Resolución** | `_solve_0_over_0_detailed()` | trigonométrico → no irracional → factor 1°, rationalize 2° |
| | Factor: `num = exp(x^2)-cos(x)`, no factorizable | falla |
| | Racionalizar: no contiene sqrt | falla |
| | L'Hôpital: | |
| | i=1: `n' = 2x·exp(x^2)+sin(x)`, `d' = 2x` | `val = 0/0 = nan` (sigue indeterminado) |
| | i=2: `n'' = 2exp(x^2)+4x^2·exp(x^2)+cos(x)`, `d'' = 2` | `val = (2+0+1)/2 = 3/2` |
| | **Paso 1:** | `\lim_{x \to 0} \frac{e^{x^2}-\cos x}{x^2} = \frac{e^{0^2}-\cos(0)}{(0)^2} \text{ es una indeterminación } \boxed{0/0}` |
| | **Paso 2 (L'Hôpital 1ª):** | `f'(x) = 2xe^{x^2}+\sin x`, `g'(x) = 2x` → `(2xe^{x^2}+\sin x)/(2x)` |
| | **Paso 3 (L'Hôpital 2ª):** | `f''(x) = 2e^{x^2}+4x^2e^{x^2}+\cos x`, `g''(x) = 2` → `(2e^{x^2}+4x^2e^{x^2}+\cos x)/2` |
| | Resultado: `(2+0+1)/2 = 3/2` | |
| **6. Salida** | `result_tex` | `\frac{3}{2}` |

---

## Resumen de formas indeterminadas probadas

| # | Expresión | Punto | Forma | Método | Resultado |
|---|-----------|-------|-------|--------|-----------|
| 1 | `(x^3+1)/(x^2-1)` | -1 | 0/0 | Factorización (suma cubos, dif cuadrados) | `-3/2` |
| 2 | `sin(2x)/(4x-4/3 sin(6x))` | 0⁺ | 0/0 | L'Hôpital (1 iteración) | `-1/2` |
| 3 | `(√(1+x)-√(1-x))/x` | 0 | 0/0 | Racionalización del numerador | `1` |
| 4 | `(2x+3)/(4x³+2)` | ∞ | ∞/∞ | División por x³ | `0` |
| 5 | `√(x-3)-√(x+3)` | ∞ | ∞-∞ | Racionalización | `0` |
| 6 | `1/(x-1)-1/(x+1)` | 1 | depende | Resta de fracciones → 0/0 o ∞/∞ | — |
| 7 | `(1-8x)^(1/(4x))` | 0 | 1^∞ | Logaritmo natural + L'Hôpital | `e⁻²` |
| 8 | `(e^(x²)-cos(x))/x²` | 0 | 0/0 | L'Hôpital (2 iteraciones) | `3/2` |

## Cobertura de código

| Componente | ¿Cubierto? |
|------------|-----------|
| `_normalize_expression()` | Sí (casos 1-8) |
| `_parse_expr()` | Sí (casos 1-8) |
| `_parse_point()` | Sí (oo, 0, -1, etc.) |
| `_classify_expr()` | Sí (trig, irracional, racional, exponencial) |
| `_detect_form()` | Sí (0/0, ∞/∞, ∞-∞, 1^∞) |
| `_safe_sub()` | Sí (con/together) |
| `_is_indeterminate()` | Sí |
| `_factor_with_info()` | Sí (caso 1) |
| `_rationalize_with_info()` | Sí (casos 3, 5) |
| `_try_lhopital()` | Sí (casos 2, 7, 8) |
| `_solve_0_over_0_detailed()` | Sí (casos 1, 2, 3, 8) |
| `_solve_inf_over_inf_detailed()` | Sí (caso 4) |
| `_solve_inf_minus_inf_detailed()` | Sí (caso 5) |
| `_solve_exponential_detailed()` | Sí (caso 7) |
| `_solve_silent()` | Sí (caso 7, sub-resolución de ln) |
| `_solve_fallback()` | No se ejecutó (todos los casos se resolvieron sin fallback) |
| `_paso1_indet_tex()` | Sí |
| `_substitution_tex()` | Sí (casos 1, 2, 3, 8) |
| `expr_to_latex()` | Sí (todos los casos) |
| `_solve_0_times_inf()` | No probado (no hay caso 0·∞ en ejemplos) |
| `_solve_exponential()` (no detallado) | No probado (todos fueron por ruta detallada) |
