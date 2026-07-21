# Prueba de Escritorio — Calculadora de Límites

Se prueban 8 ejercicios que cubren todas las formas indeterminadas y tipos de límite. Para cada uno se muestra el flujo completo: entrada → parseo → clasificación → detección → resolución paso a paso → salida.

---

## Caso 1: Límite algebraico racional — Factorización (0/0)

**Entrada:**
```
expresión = (x^3+1)/(x^2-1)
tendencia = x
valor     = -1
```

### Traza

| Etapa | Acción | Resultado |
|-------|--------|-----------|
| **1. Parseo** | `_normalize_expression()` + `sympify()` | `(x^3 + 1)/(x^2 - 1)` |
| | `_parse_point("-1")` | `-1` (Rational) |
| **2. Clasificación** | `_classify_expr()` — sin trig, log, e, sqrt, exponente variable. Polinomios. | `"algebraico racional"` |
| **3. Sustitución directa** | `_safe_sub(expr, -1)` → num=0, den=0 → `nan` | **Indeterminado** |
| **4. Detectar forma** | `_detect_form()` → together → num=0, den=0 | `"0/0"` |
| **5. Resolución** | `_solve_0_over_0_detailed()` — tipo algebraico racional → intenta factorizar |
| **Paso 1** | `_paso1_indet_tex()` | `\lim_{x \to -1} \frac{x^3+1}{x^2-1} = \frac{(-1)^3+1}{(-1)^2-1} \text{ es una indeterminación } \boxed{0/0}` |
| **Factorizar** | `_factor_with_info()` | num: `(x+1)(x^2-x+1)` tipo **suma de cubos** |
| | | den: `(x-1)(x+1)` tipo **diferencia de cuadrados** |
| | `simplified = cancel(...)` | `(x^2 - x + 1)/(x - 1)` |
| | `val = _safe_sub(simplified, -1)` | `-3/2` (no indeterminado) |
| **Paso 2** | Descripción | `'Se factoriza el numerador (suma de cubos) y el denominador (diferencia de cuadrados)'` |
| | LaTeX | `\frac{x^3+1}{x^2-1} = \frac{(x+1)(x^2-x+1)}{(x-1)(x+1)} = \frac{x^2-x+1}{x-1}` |
| **Paso 3** | Descripción | `'Se sustituye el valor de la tendencia de x para hallar el límite.'` |
| | LaTeX | `\lim_{x \to -1} \frac{x^2-x+1}{x-1} = \frac{(-1)^2-(-1)+1}{(-1)-1} = -\frac{3}{2} \\ \boxed{\lim_{x \to -1} \frac{x^3+1}{x^2-1} = -\frac{3}{2}}` |
| **6. Salida** | result_tex=`- \frac{3}{2}`, form=`0/0`, limit_type=`algebraico racional` |

---

## Caso 2: Límite algebraico irracional — Racionalización (0/0)

**Entrada:** `(sqrt(1+x)-sqrt(1-x))/x`, tendencia=x, valor=0

### Traza

| Etapa | Resultado |
|-------|-----------|
| **Parseo** | `(sqrt(x+1) - sqrt(1-x))/x` |
| **Clasificación** | Contiene sqrt → `"algebraico irracional"` |
| **Sustitución** | `(1-1)/0 = 0/0` → nan → indeterminado |
| **Forma** | `"0/0"` |
| **Paso 1** | `\lim_{x \to 0} \frac{\sqrt{1+x}-\sqrt{1-x}}{x} = \frac{\sqrt{1+0}-\sqrt{1-0}}{0} \text{ es una indeterminación } \boxed{0/0}` |
| **Racionalizar** | Conjugado = `sqrt(x+1)+sqrt(1-x)`. new_expr = `2/(sqrt(x+1)+sqrt(1-x))`. val = `1` |
| **Paso 2** | `'Se racionaliza el numerador para eliminar la indeterminación.'` |
| **Paso 3** | `\boxed{\lim_{x \to 0} \frac{\sqrt{1+x}-\sqrt{1-x}}{x} = 1}` |
| **Salida** | result=`1`, form=`0/0`, type=`algebraico irracional` |

---

## Caso 3: Límite trigonométrico — Límites especiales (0/0)

**Entrada:** `sin(2*x)/(4*x-4/3*sin(6*x))`, tendencia=x, valor=0

### Traza

| Etapa | Resultado |
|-------|-----------|
| **Parseo** | `sin(2x) / (4x - 4·sin(6x)/3)` |
| **Clasificación** | Contiene sin → `"trigonométrico"` |
| **Sustitución** | `sin(0)/(0 - 4/3·sin(0)) = 0/0` → nan |
| **Forma** | `"0/0"` |
| **Paso 1** | `\lim_{x \to 0} \frac{\sin(2x)}{4x-\frac{4}{3}\sin(6x)} = \frac{\sin(2(0))}{4(0)-\frac{4}{3}\sin(6(0))} \text{ es una indeterminación } \boxed{0/0}` |
| **Paso 2** | Muestra los 3 límites trigonométricos especiales: |
| | `\lim_{u\to 0} \frac{\sin u}{u}=1 \quad \lim_{u\to 0} \frac{u}{\sin u}=1 \quad \lim_{u\to 0} \frac{1-\cos u}{u}=0` |
| | Descripción: `'Se utilizan límites trigonométricos fundamentales.'` |
| **Paso 3** | `\boxed{\lim_{x \to 0} \frac{\sin(2x)}{4x-\frac{4}{3}\sin(6x)} = -\frac{1}{2}}` |
| | Internamente se usa `_solve_silent()` (L'Hôpital sin mostrar pasos) |
| **Salida** | result=`-1/2`, form=`0/0`, type=`trigonométrico` |

---

## Caso 4: Límite logarítmico — Límite especial con e (0/0)

**Entrada:** `(e^(x^2)-cos(x))/(x^2)`, tendencia=x, valor=0

### Traza

| Etapa | Resultado |
|-------|-----------|
| **Parseo** | `(exp(x^2) - cos(x))/x^2` |
| **Clasificación** | Contiene `e` (constante de Euler) → `"logarítmico"` |
| **Sustitución** | `(1-1)/0 = 0/0` → nan |
| **Forma** | `"0/0"` |
| **Paso 1** | `\lim_{x \to 0} \frac{e^{x^2}-\cos x}{x^2} = \frac{e^{0^2}-\cos(0)}{0^2} \text{ es indeterminación } \boxed{0/0}` |
| **Paso 2** | Muestra el límite especial: `\lim_{u\to 0} \frac{e^u-1}{u}=1` |
| | Descripción: `'Se utiliza el límite logarítmico fundamental.'` |
| **Paso 3** | `\boxed{\lim_{x \to 0} \frac{e^{x^2}-\cos x}{x^2} = \frac{3}{2}}` |
| **Salida** | result=`3/2`, form=`0/0`, type=`logarítmico` |

---

## Caso 5: Límite exponencial — Identidad fundamental (1^∞)

**Entrada:** `(1-8*x)^(1/(4*x))`, tendencia=x, valor=0

### Traza

| Etapa | Resultado |
|-------|-----------|
| **Parseo** | `(1-8x)^(1/(4x))` |
| **Clasificación** | Variable en exponente → `"exponencial"` |
| **Sustitución** | `1^∞` → fuerza indeterminado |
| **Forma** | `"1^∞"` |
| **Paso 1** | `\lim_{x \to 0} (1-8x)^{\frac{1}{4x}} = (1-8(0))^{\frac{1}{4(0)}} \text{ es indeterminación } \boxed{1^\infty}` |
| **Paso 2** | Aplica identidad: `\lim f^g = e^{\lim (f-1)·g}` |
| | `(1-8x-1)·(1/(4x)) = (-8x)·(1/(4x)) = -2` |
| | Descripción: `'Se aplica la igualdad fundamental de límites exponenciales.'` |
| **Paso 3** | `\lim (1-8x)^{\frac{1}{4x}} = e^{-2} \\ \boxed{\lim_{x \to 0} (1-8x)^{\frac{1}{4x}} = e^{-2}}` |
| **Salida** | result=`e^{-2}`, form=`1^∞`, type=`exponencial` |

---

## Caso 6: Límite ∞/∞ — División por máxima potencia

**Entrada:** `(2*x+3)/(4*x**3+2)`, tendencia=x, valor=oo

### Traza

| Etapa | Resultado |
|-------|-----------|
| **Parseo** | `(2x+3)/(4x^3+2)` |
| **Clasificación** | Polinomios → `"algebraico racional"` |
| **Sustitución** | `∞/∞` → nan |
| **Forma** | `"∞/∞"` |
| **Paso 1** | `\lim_{x \to \infty} \frac{2x+3}{4x^3+2} \text{ es indeterminación } \boxed{\infty/\infty}` |
| **Paso 2** | grado num=1, grado den=3 → n=3. Dividir entre `x^3` |
| | `\frac{2x+3}{4x^3+2} = \frac{2/x^2 + 3/x^3}{4 + 2/x^3}` |
| **Paso 3** | `\boxed{\lim_{x \to \infty} \frac{2x+3}{4x^3+2} = 0}` |
| **Salida** | result=`0`, form=`∞/∞`, type=`algebraico racional` |

---

## Caso 7: Límite ∞-∞ irracional — Racionalización

**Entrada:** `sqrt(x-3)-sqrt(x+3)`, tendencia=x, valor=oo

### Traza

| Etapa | Resultado |
|-------|-----------|
| **Parseo** | `sqrt(x-3) - sqrt(x+3)` |
| **Clasificación** | Contiene sqrt → `"algebraico irracional"` |
| **Sustitución** | `∞-∞` → nan |
| **Forma** | `"∞-∞"` |
| **Paso 1** | `\lim_{x \to \infty} \sqrt{x-3}-\sqrt{x+3} \text{ es indeterminación } \boxed{\infty - \infty}` |
| **Paso 2** | Conjugado = `sqrt(x-3)+sqrt(x+3)`. Resultado: `-6/(sqrt(x-3)+sqrt(x+3))` |
| | Descripción: `'Se racionaliza el numerador.'` |
| **Paso 3** | `\boxed{\lim_{x \to \infty} \sqrt{x-3}-\sqrt{x+3} = 0}` |
| **Salida** | result=`0`, form=`∞-∞`, type=`algebraico irracional` |

---

## Resumen de resultados

| # | Expresión | Punto | Tipo | Forma | Método | Resultado |
|---|-----------|-------|------|-------|--------|-----------|
| 1 | `(x³+1)/(x²-1)` | -1 | algebraico racional | 0/0 | Factorizar (suma cubos, dif cuadrados) | `-3/2` |
| 2 | `(√(1+x)-√(1-x))/x` | 0 | algebraico irracional | 0/0 | Racionalizar numerador | `1` |
| 3 | `sin(2x)/(4x-4/3·sen6x)` | 0 | trigonométrico | 0/0 | Límites trigonométricos especiales | `-1/2` |
| 4 | `(eˣ²-cos x)/x²` | 0 | logarítmico | 0/0 | Límite especial (e^u-1)/u | `3/2` |
| 5 | `(1-8x)^(1/4x)` | 0 | exponencial | 1^∞ | Identidad lim f^g = e^(lim (f-1)·g) | `e⁻²` |
| 6 | `(2x+3)/(4x³+2)` | ∞ | algebraico racional | ∞/∞ | Dividir por x³ | `0` |
| 7 | `√(x-3)-√(x+3)` | ∞ | algebraico irracional | ∞-∞ | Racionalizar | `0` |

## Cobertura de código

| Componente | Probado en casos |
|------------|-----------------|
| `_normalize_expression()` | 1–7 |
| `_parse_expr()` / `_parse_point()` | 1–7 |
| `_classify_expr()` | 1: racional, 2: irracional, 3: trig, 4: log, 5: exp, 6: racional, 7: irracional |
| `_detect_form()` | 1–2: 0/0, 3–4: 0/0, 5: 1^∞, 6: ∞/∞, 7: ∞-∞ |
| `_safe_sub()` + `_is_indeterminate()` | 1–7 |
| `_factor_with_info()` | 1 (suma cubos + dif cuadrados) |
| `_rationalize_with_info()` | 2, 7 |
| `_solve_trigonometric_0_over_0()` | 3 |
| `_solve_logarithmic_0_over_0()` | 4 |
| `_solve_exponential_detailed()` | 5 |
| `_solve_inf_over_inf_detailed()` | 6 |
| `_solve_inf_minus_inf_detailed()` | 7 |
| `_solve_silent()` | 3, 4 (cálculo interno sin pasos visibles) |
| `_try_lhopital()` | 3, 4 (usado internamente por _solve_silent) |
| `_substitution_tex()` | 1–5 (puntos finitos), 6–7 (∞ → None) |
| `_paso1_indet_tex()` | 1–7 |
| `expr_to_latex()` | 1–7 |
| `_detect_factor_type()` | 1: suma cubos, dif cuadrados |
| `_solve_fallback()` | No necesario (todos resueltos sin fallback) |
