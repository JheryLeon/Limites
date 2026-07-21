# Manual de Usuario — Calculadora de Límites

Aplicación web para resolver límites paso a paso, cubriendo todas las formas indeterminadas (0/0, ∞/∞, ∞-∞, 0·∞, 1^∞, 0^0, ∞^0).

---

## 1. Requisitos

- **Python 3.8 o superior** instalado
- **pip** (gestor de paquetes de Python, incluido con Python)
- **Git** (opcional, para clonar el repositorio)
- Conexión a internet (solo para la primera instalación)

---

## 2. Instalación

### Opción A: Descargar desde GitHub

1. Abre una terminal (PowerShell en Windows, Terminal en macOS/Linux)

2. Clona el repositorio:
   ```bash
   git clone https://github.com/JheryLeon/Limites.git
   ```

3. Entra a la carpeta:
   ```bash
   cd Limites
   ```

4. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

### Opción B: Copiar la carpeta manualmente

Si te pasaron la carpeta del proyecto comprimida:

1. Descomprime el archivo en una ubicación de tu preferencia
2. Abre una terminal en esa carpeta
3. Ejecuta:
   ```bash
   pip install flask sympy gunicorn
   ```

---

## 3. Ejecutar la aplicación

En la terminal, dentro de la carpeta del proyecto:

```bash
python app.py
```

Verás un mensaje como:
```
* Running on http://127.0.0.1:5000
```

Abre tu navegador web y ve a: **http://127.0.0.1:5000**

Para detener el servidor, presiona `Ctrl + C` en la terminal.

---

## 4. Cómo usar la calculadora

### 4.1 Pantalla principal

Al abrir la aplicación verás:

```
┌─────────────────────────────────────┐
│  ∫ Calculadora de Límites           │
│  Paso a paso · Todas las indetermin.│
├─────────────────────────────────────┤
│  Expresión: [____________________]  │
│  [x²] [x³] [xⁿ] [√] [/] [·] [( )] │
│  Vista Previa del Ejercicio         │
│                                     │
│  Tendencia: [x]  Valor: [0] [∞]    │
│                                     │
│  [ Calcular el límite ]             │
│                                     │
│  Ejemplos rápidos:                  │
│  [ (x³+1)/(x²-1) ] [ (x²-2x)/... ] │
│  [ (√(1+x)-√(1-x))/x ] ...         │
└─────────────────────────────────────┘
```

### 4.2 Ingresar una expresión

Escribe la expresión en el campo **Expresión**. Puedes usar:

| Símbolo | Cómo escribirlo | Ejemplo |
|---------|----------------|---------|
| Potencia | `^` o `**` | `x^2`, `x**3` |
| Raíz cuadrada | `sqrt()` o botón √ | `sqrt(x+1)` |
| Fracción | `/` | `(x+1)/(x-2)` |
| Multiplicación | `*` o `·` | `2*x`, `3·sin(x)` |
| Número e | `e` o botón e | `e^(x^2)` |
| Infinito | `oo` o botón ∞ | punto: `oo` |
| Pi | `pi` o botón π | `sin(pi*x)` |
| Función seno | `sin()` | `sin(2*x)` |
| Función coseno | `cos()` | `cos(x^2)` |
| Función tangente | `tan()` | `tan(3*x)` |
| Logaritmo natural | `ln()` o `log()` | `ln(x)` |
| Logaritmo base 10 | `log10()` | `log10(x)` |
| Valor absoluto | `abs()` o botón \|x\| | `abs(x-1)` |
| Paréntesis | `(` `)` o botón ( ) | `(x^2-4)` |
| Corchetes | `[` `]` o botón [ ] | `[x]` (se convierten a paréntesis) |

La **Vista Previa** muestra cómo se interpretará tu expresión antes de calcular.

### 4.3 Configurar tendencia y valor

- **Tendencia**: la variable del límite (normalmente `x`). Puedes cambiarla a `t`, `u`, etc.
- **Valor**: el punto al que tiende la variable. Ejemplos:
  - `0` → x → 0
  - `oo` (o ∞) → x → ∞
  - `-oo` → x → -∞
  - `pi` → x → π
  - `1`, `-1`, `2`, etc. → números concretos

### 4.4 Ejemplos rápidos

Haz clic en cualquier botón de **Ejemplos rápidos** para cargar automáticamente una expresión y su valor. Luego puedes modificar la expresión si lo deseas.

---

## 5. Interpretar los resultados

Después de hacer clic en **Calcular el límite**, verás:

```
┌─ Resultado ─────────────────────────┐
│                                      │
│  límite algebraico racional   0/0   │  ← tipo y forma
│  ┌─────────────────────────────┐    │
│  │  \boxed{4}                  │    │  ← resultado
│  └─────────────────────────────┘    │
│                                      │
│  ❶ Paso 1                           │
│  Se sustituye la tendencia...       │
│  \lim_{x \to 2} ...                  │
│                                      │
│  ❷ Paso 2                           │
│  Se factoriza el numerador          │
│  (diferencia de cuadrados)          │
│  \frac{x^2-4}{x-2} = ...            │
│                                      │
│  ❸ Paso 3                           │
│  Se sustituye el valor...            │
│  \boxed{\lim_{x \to 2} ... = 4}     │
└──────────────────────────────────────┘
```

### Tipos de límite que se muestran

| Tipo | Significado |
|------|-------------|
| **límite algebraico racional** | Fracción de polinomios |
| **límite algebraico irracional** | Contiene raíces cuadradas |
| **límite trigonométrico** | Contiene sen, cos, tan, etc. |
| **límite logarítmico** | Contiene el número `e` (Euler) |
| **límite exponencial** | Variable en el exponente |

### Formas indeterminadas

| Forma | Significado |
|-------|-------------|
| **0/0** | Cero entre cero |
| **∞/∞** | Infinito entre infinito |
| **∞-∞** | Infinito menos infinito |
| **0·∞** | Cero por infinito |
| **1^∞** | Uno elevado a infinito |
| **0^0** | Cero elevado a cero |
| **∞^0** | Infinito elevado a cero |

---

## 6. Métodos de resolución por tipo

| Tipo | Paso 2 | Ejemplo |
|------|--------|---------|
| Algebraico racional (0/0) | Factorizar (diferencia de cuadrados, suma/diferencia de cubos) | `(x²-4)/(x-2)` |
| Algebraico irracional (0/0) | Racionalizar | `(√(1+x)-√(1-x))/x` |
| Trigonométrico (0/0) | Límites especiales: `sen(u)/u=1`, `u/sen(u)=1`, `(1-cos u)/u=0` | `sen(2x)/(4x-4/3·sen6x)` |
| Logarítmico (0/0) | Límite especial: `(e^u-1)/u=1` | `(eˣ²-cos x)/x²` |
| Exponencial (1^∞) | Identidad: `lim f^g = e^(lim (f-1)·g)` | `(1-8x)^(1/4x)` |
| ∞/∞ | Dividir por la máxima potencia | `(2x+3)/(4x³+2)` |
| ∞-∞ (con raíz) | Racionalizar | `√(x-3)-√(x+3)` |
| ∞-∞ (racional) | Restar fracciones | `1/(x-1)-1/(x+1)` |

---

## 7. Solución de problemas

### Error: "No se pudo interpretar el punto"
Asegúrate de que el valor del punto sea válido: `0`, `oo`, `-oo`, `pi`, o un número.

### Error: "Error al parsear la expresión"
Revisa que la expresión esté bien escrita. Usa `*` para multiplicación explícita (`2*x`, no `2x`).

### La vista previa no se actualiza
Asegúrate de tener conexión a internet (KaTeX se carga desde CDN).

### La página se ve sin formato
Verifica que los estilos CSS se carguen correctamente. Si usas un navegador antiguo, actualízalo.

### No se muestra el resultado
Puede que el límite sea demasiado complejo para los métodos automáticos. El programa usa SymPy como respaldo.

---

## 8. Despliegue en Render (producción)

Para publicar la calculadora en internet gratis:

1. Sube el proyecto a GitHub
2. Crea cuenta en https://dashboard.render.com
3. New → Web Service → conecta tu repositorio
4. Configura:

   | Campo | Valor |
   |-------|-------|
   | Name | `calculadora-limites` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn app:app` |
   | Plan | **Free** ($0/mes) |

5. Clic en **Create Web Service**. En 3-5 minutos tendrás una URL pública.

---

## 9. Archivos del proyecto

| Archivo | Función |
|---------|---------|
| `app.py` | Servidor web Flask (rutas, formularios) |
| `solver.py` | Motor de resolución de límites (SymPy) |
| `templates/index.html` | Interfaz de usuario (HTML + JavaScript + KaTeX) |
| `static/style.css` | Estilos visuales |
| `requirements.txt` | Dependencias (Flask, SymPy, Gunicorn) |
| `Procfile` | Configuración para Render |
| `docs/diagrama_flujo.md` | Diagrama de flujo del programa |
| `docs/prueba_escritorio.md` | Prueba de escritorio con casos de prueba |
