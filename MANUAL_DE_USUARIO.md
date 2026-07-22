# Manual de Usuario — Calculadora de Límites

Aplicación web para resolver límites paso a paso, cubriendo todas las formas indeterminadas (0/0, ∞/∞, ∞-∞, 0·∞, 1^∞, 0^0, ∞^0).

---

## 1. Instalar Python (si no lo tienes)

Si tu computadora ya tiene Python instalado, salta al paso 2.

### Windows

1. Ve a Python https://www.python.org/ftp/python/3.14.6/python-3.14.6-amd64.exe
2. Una vez descargado, **abre el archivo** `python-3.x.x-amd64.exe`
3. **IMPORTANTE**: En la primera pantalla, **marca la casilla** que dice:
   > ✅ **Add Python to PATH**
4. Luego haz clic en **Install Now**
5. Espera a que termine la instalación (1-2 minutos)
6. Al finalizar, haz clic en **Close**

### macOS

1. Abre la terminal (busca "Terminal" en Spotlight)
2. Escribe el siguiente comando y presiona Enter:
   ```bash
   xcode-select --install
   ```
3. Sigue las instrucciones en pantalla para instalar las herramientas de desarrollo
4. Luego instala Python desde https://www.python.org/downloads/ — descarga el instalador para macOS y ábrelo

### Linux (Ubuntu/Debian)

Abre la terminal y ejecuta:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

## 2. Verificar que Python se instaló correctamente

### Windows

1. Presiona `Windows + R`, escribe `powershell` y presiona Enter
2. Escribe los siguientes comandos, uno por uno:

```powershell
python --version
```

Deberías ver algo como: `Python 3.12.0`

```powershell
pip --version
```

Deberías ver algo como: `pip 24.0 from ...`

> **Si el primer comando da error**, prueba con:
> ```powershell
> python3 --version
> py --version
> ```

### macOS / Linux

En la terminal:

```bash
python3 --version
pip3 --version
```

---

## 3. Descargar el proyecto

Tienes dos opciones:

### Opción A: Descargar ZIP (recomendado para principiantes)

1. Abre tu navegador y ve a: https://github.com/JheryLeon/Limites
2. Haz clic en el botón verde **Code** (arriba a la derecha)
3. Selecciona **Download ZIP**
4. Una vez descargado, haz clic derecho sobre el archivo ZIP → **Extraer todo** (Windows) o haz doble clic para descomprimirlo (macOS)
5. Se creará una carpeta llamada `Limites` o `Limites-main`

### Opción B: Clonar con Git (si ya tienes Git instalado)

Abre la terminal y escribe:

```bash
git clone https://github.com/JheryLeon/Limites.git
cd Limites
```

---

## 4. Abrir la terminal en la carpeta del proyecto

### Windows

1. Abre la carpeta `Limites` que acabas de descomprimir
2. Haz clic en la **barra de direcciones** del explorador de archivos (la barra blanca de arriba donde dice la ruta)
3. Escribe `powershell` y presiona Enter
4. Se abrirá una ventana azul de PowerShell **ya dentro de la carpeta correcta**

### macOS / Linux

En la terminal, navega hasta la carpeta:

```bash
cd ~/Descargas/Limites   # ajusta la ruta según donde descargaste
```

O simplemente escribe `cd` y arrastra la carpeta a la terminal, luego presiona Enter.

---

## 5. Instalar las dependencias

Estando en la terminal **dentro de la carpeta del proyecto**, escribe:

### Windows (PowerShell)

```powershell
pip install -r requirements.txt
```

### macOS / Linux

```bash
pip3 install -r requirements.txt
```

Este comando instalará Flask (el servidor web), SymPy (cálculo simbólico) y Gunicorn.

> **Si aparece un error** de permisos, prueba:
> ```bash
> pip install --user -r requirements.txt
> ```
>
> **Si en Windows aparece un error** sobre `execution policy`, ejecuta primero:
> ```powershell
> Set-ExecutionPolicy Unrestricted -Scope CurrentUser
> ```

La instalación puede tardar **2-5 minutos** porque SymPy es una librería grande (~40 MB). Espera a que termine. Verás algo como:

```
Successfully installed flask-3.x.x sympy-1.x.x gunicorn-20.x.x
```

---

## 6. Ejecutar la aplicación

### Windows (PowerShell)

En la misma terminal, escribe:

```powershell
python app.py
```

### macOS / Linux

```bash
python3 app.py
```

Si todo funciona bien, verás un mensaje como:

```
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

---

## 7. Abrir la calculadora en el navegador

1. Abre **Google Chrome, Microsoft Edge, Firefox o Safari**
2. En la barra de direcciones (arriba), escribe: **http://127.0.0.1:5000**
3. Presiona Enter

¡Ya deberías ver la Calculadora de Límites funcionando!

> La aplicación solo funciona mientras la terminal esté abierta. Para cerrarla, presiona `Ctrl + C` en la terminal.

---

## 8. Solución de problemas comunes

### "python no se reconoce como un comando"

**Causa**: Python no está agregado al PATH (ruta del sistema).

**Solución**: Desinstala Python y vuelve a instalarlo. En la primera pantalla del instalador, **asegúrate de marcar "Add Python to PATH"**.

### "pip no se reconoce como un comando"

**Solución**:

- Windows: Prueba con `python -m pip install -r requirements.txt`
- macOS/Linux: Prueba con `pip3` en lugar de `pip`

### Error "No module named flask"

**Causa**: No se instalaron las dependencias (o se instalaron en el lugar equivocado).

**Solución**: Asegúrate de estar en la carpeta del proyecto y ejecuta de nuevo:

```bash
pip install -r requirements.txt
```

### Error "Address already in use"

**Causa**: El puerto 5000 ya está ocupado por otro programa.

**Solución**: Cierra otros programas o cambia el puerto:

```bash
python app.py --port=5001
```

Luego abre el navegador en `http://127.0.0.1:5001`

### El mensaje "Running on ..." no aparece

**Causa**: El programa se ejecutó pero no se ve el mensaje.

**Solución**: Revisa si hay errores en la terminal. Si ves mensajes en rojo, comparte esos mensajes con tu profesor.

### Si todo lo demás falla

Prueba desinstalar Python completamente y volver a instalarlo desde cero, siguiendo el paso 1 al pie de la letra.

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
