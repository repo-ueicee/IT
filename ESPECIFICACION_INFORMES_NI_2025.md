# Especificación final — Informes HTML imprimibles A4
## Evaluación de Alfabetización y Matemática en niños de 5 años — Nivel Inicial 2025
## GCBA / UEICEE

---

## 1. Estructura general del informe

Cada informe es un HTML imprimible con:

- Páginas A4 fijas (210mm × 297mm).
- Header gráfico institucional (`image1.png`, 18.7mm de alto).
- Footer gráfico institucional (`image2.png`, 26.6mm de alto).
- Número de página en la esquina inferior derecha.
- Cuerpo central (`.pbody`) con contenido.
- Sin overflow: ningún contenido debe pisar el footer ni cortarse entre páginas.
- Cada bloque de contenido es indivisible: título + cuadro + nota + margen inferior.

Tipografía: Archivo (Google Fonts). Paleta institucional: azul navy `#153244`, cyan `#8DE2D6`, amarillo `#FFCC00`.

---

## 2. Encabezado del informe (página 1)

- Pastilla azul navy con texto blanco: `UEICEE (UNIDAD DE EVALUACIÓN INTEGRAL DE LA CALIDAD Y EQUIDAD EDUCATIVA)`.
- Nombre del establecimiento en negrita grande.
- Título: `Resultados de la Evaluación "Alfabetización y Matemática - Sala de 5 años"`.
- Pills: cantidad de niños evaluados + cantidad de salas.
- Usar "sala" / "salas" (no "salita" / "salitas").

---

## 3. Introducción

Recuadro celeste claro con borde cyan:

> **INTRODUCCIÓN**
>
> Con la intención de ofrecer información para la mejora de los aprendizajes y la enseñanza en el nivel inicial, se presentan los resultados obtenidos por el establecimiento en la evaluación de aprendizajes de **Alfabetización y Matemática en niños de 5 años - 2025**.
>
> Los resultados se brindan para el total del jardín y por sala, considerando para cada área:
> - **Puntaje promedio** del conjunto de niños en cada contenido evaluado: **0 a 4 puntos**.
> - **Nivel de logro** en el que se ubican los niños en cada contenido: del **0 (nivel previo)** al **4 (meta del DC)**.

---

## 4. Subtítulos redundantes — ELIMINADOS

En todas las páginas, se elimina el subtítulo corto ("Alfabetización" / "Matemática") que aparecía debajo del nombre del jardín (`.psub`). Se mantienen los títulos de sección ("Alfabetización: nivel de logro en cada contenido.", etc.).

---

## 5. Tablas de puntaje promedio

Una tabla por área (Alfabetización y Matemática). Columnas:

| Contenido | Descripción | Total jardín | Sala 1 | Sala 2 | ... |

- En jardines de 1 sala: sin columna "Total jardín" (redundante).
- Fuente base: 8pt (escala con el auto-fit por página).
- Contenidos en negrita 8.5pt, descripciones 8.5pt, puntajes 9.5pt.
- Los nombres de salas en los encabezados pueden ocupar más de una línea.

---

## 6. Cuadros de niveles de logro (reemplazan gráficos de barras)

Para cada contenido evaluado, un cuadro/tabla con:

**Columnas:** Niveles | Nivel 0 | Nivel 1 | Nivel 2 | Nivel 3 | Nivel 4

**Filas:** Total jardín + una fila por sala. En jardines de 1 sala, NO mostrar "Total jardín".

**Celdas:** `absoluto (%)` — ejemplo: `8 (7%)`.

**Colores de fondo por nivel:**
- Nivel 0: salmón claro `#f2a99e`
- Nivel 1: rojo medio `#d44040`
- Nivel 2: naranja `#e0700f`
- Nivel 3: amarillo `#f4c430`
- Nivel 4: verde `#82c9a0`

**Texto:** azul navy `#153244`, seminegrita.

**Nombre de sala en una sola línea** (`white-space: nowrap`).

**Fila "Total jardín":** fondo amarillo `#FFCC00`, texto navy.

---

## 7. Títulos de cuadros

Formato: **Contenido:** descriptor.

Ejemplo: **Correspondencias:** Relacionar los sonidos de las palabras con las letras que los representan.

---

## 8. Nota al pie de cada cuadro

Debajo de cada cuadro: `Nivel 4 esperado según DC: [descriptor]`.

---

## 9. Separación entre áreas

- Matemática empieza siempre en hoja nueva.
- Nunca mezclar Alfabetización y Matemática en la misma página.

---

## 10. Títulos de sección

`.area-title` con fondo celeste claro, borde izquierdo cyan, 10pt negrita:
- "Alfabetización: puntaje promedio por contenido."
- "Alfabetización: nivel de logro en cada contenido."
- "Matemática: puntaje promedio por contenido."
- "Matemática: nivel de logro en cada contenido."

---

## 11. Orden de contenidos

**Alfabetización (8 contenidos):**
1. Uso de la escritura
2. Correspondencias
3. Vocabulario
4. Oralidad
5. Escritura
6. Conciencia fonológica
7. Comprensión
8. Lectura

**Matemática (7 contenidos):**
1. Espacio
2. Serie numérica
3. Conteo
4. Escritura de números
5. Situaciones aditivas
6. Reconocimiento de números
7. Figuras geométricas

---

## 12. Pisos mínimos de legibilidad

| Elemento | Mínimo general | 1 sala (más generoso) |
|----------|---------------|-----------------------|
| `.dim-title` | 9pt | 10–11pt |
| `.lvl-table td` | 8.5pt | 9.5–10.5pt |
| `.lvl-table th` | 8pt | 9–10pt |
| `.td-agg` | 8.3pt | — |
| `.dim-note` | 7.5pt | 8–9pt |

---

## 13. Regla visual global

**Hacer los cuadros lo más grandes posible sin overflow.**

En cada página:
1. Calcular espacio disponible.
2. Si sobra espacio → aumentar fuente, padding, line-height, espaciado entre bloques.
3. Validar overflow.
4. Repetir hasta ocupar razonablemente el alto útil sin pasarse.

No aceptar tablas miniaturizadas con mucho espacio en blanco.

---

## 14. Distribución por cantidad de salas

### CASO 1: jardines con 1 sala (5 páginas)

- **P1:** Intro + tabla Alfa + Uso de la escritura.
- **P2:** Correspondencias, Vocabulario, Oralidad, Escritura (4 cuadros).
- **P3:** Conciencia fonológica, Comprensión, Lectura (3 cuadros).
- **P4:** Tabla Mate + Espacio, Serie numérica (2 cuadros).
- **P5:** Conteo, Escritura de números, Situaciones aditivas, Reconocimiento de números, Figuras geométricas (5 cuadros).

No mostrar fila "Total jardín". Fuentes generosas (10–11pt).

### CASO 2: jardines con 2 salas (5 páginas)

- **P1:** Intro + tabla Alfa + Uso de la escritura.
- **P2:** Correspondencias, Vocabulario, Oralidad, Escritura.
- **P3:** Conciencia fonológica, Comprensión, Lectura.
- **P4:** Tabla Mate + Espacio, Serie numérica, Conteo.
- **P5:** Escritura de números, Situaciones aditivas, Reconocimiento de números, Figuras geométricas.

### CASO 3–4: jardines con 3 o 4 salas (7 páginas)

- **P1:** Intro + tabla Alfa (sin cuadros). Tabla expandida para ocupar el espacio.
- **P2:** Uso de la escritura, Correspondencias, Vocabulario (3 cuadros).
- **P3:** Oralidad, Escritura, Conciencia fonológica (3 cuadros).
- **P4:** Comprensión, Lectura (2 cuadros).
- **P5:** Tabla Mate + Espacio (1 cuadro).
- **P6:** Serie numérica, Conteo, Escritura de números (3 cuadros).
- **P7:** Situaciones aditivas, Reconocimiento de números, Figuras geométricas (3 cuadros).

### CASO 5–6: jardines con 5 o 6 salas (7 páginas)

Misma estructura que 3–4, con ajuste fino:
- P1: tabla Alfa levemente comprimida (5 salas: −7mm, 6 salas: −11mm) para no pisar el número de página.
- Tabla Mate separada de los cuadros (sin cuadros en la página de la tabla Mate).

### CASO 7+: jardines con 7 o más salas (10 páginas)

- **P1:** Intro + tabla Alfa (sin cuadros). Tipografía ajustada para tabla con 8+ columnas.
- **P2–P5:** Alfa con 2 cuadros por página (bloques muy altos con 8 filas).
- **P6:** Tabla Mate (sin cuadros).
- **P7–P10:** Mate con 2 cuadros por página + 1 cuadro final.

---

## 15. Ajustes condicionales para tablas de promedios (P1)

**5 salas:** padding reducido, contenido 10pt, descripción 9pt.
**6 salas:** contenido 8.8pt, descripción 8pt, puntajes 8pt, padding 0.7mm.
**7+ salas:** título sección 9pt, contenido 7.5pt, descripción 7pt, puntajes 6.5pt.

---

## 16. Auto-fit con render real (Playwright)

El generador usa Playwright (Chromium headless) para:
1. Renderizar cada informe.
2. Medir `scrollHeight - clientHeight` por página.
3. Si hay overflow → reducir el factor de escala de esa página (bisección).
4. Iterar hasta convergencia (máx 20 iteraciones).
5. Cachear los factores óptimos por cantidad de salas para generación en lote.

---

## 17. Archivos del sistema

| Archivo | Descripción |
|---------|-------------|
| `generar_informes.py` | Generador Python principal |
| `datos_para_informes_claude.txt` | Datos de jardines privados (60) |
| `datos_para_informes_estatal_claude.txt` | Datos de jardines estatales (346) |
| `image1.png` | Header institucional |
| `image2.png` | Footer institucional |
| `cached_factors.json` | Factores de escala calibrados por cantidad de salas |

### Requisitos para ejecutar:
```
pip install playwright
python -m playwright install chromium
python generar_informes.py                    # genera todos
python generar_informes.py "nombre jardín"    # genera uno específico
```

---

## 18. Validaciones obligatorias

Antes de finalizar cada informe:
- [ ] Ninguna página tiene overflow.
- [ ] Ningún bloque pisa el footer.
- [ ] Ningún bloque queda cortado entre páginas.
- [ ] Matemática empieza siempre en hoja nueva.
- [ ] Alfa y Mate no se mezclan en la misma página.
- [ ] En 1 sala no aparece "Total jardín".
- [ ] No hay tablas miniaturizadas con mucho blanco.
- [ ] Las notas de Nivel 4 son legibles.
- [ ] Los nombres de sala aparecen en una sola línea en los cuadros.
