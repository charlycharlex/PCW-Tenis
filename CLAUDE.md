# PCW Tenis — landing con los tenis firmados

## El proyecto

Landing para **Palmer Cooper Wallace** (agencia de marketing, https://palmercooperwallace.com/).
Cada vez que la agencia termina un proyecto, el cliente les firma unos tenis. La landing muestra
esos tenis en 3D como una forma innovadora de enseñar con qué marcas han trabajado.

- **4 pares = 8 tenis**, escaneados en 3D (fotogrametría, `.usdz`).
- Solo importan las firmas de **las marcas grandes**; el resto de mensajes es textura.
- Referencia de interacción: https://www.eathungrytiger.com/ — el objeto 3D se anima conforme
  se hace scroll. Además se quiere poder **girar cada tenis 360°** para verlo.

Precedente propio: la landing de EzEat (`C:\Users\charl\Documents\Landingezeat`) ya usa el
mismo stack (three.js + GSAP + Draco, un solo `index.html` sin compilación, pellizco en celular,
fallback si no hay WebGL). Reusar sus patrones.

## Estado actual (2026-10-14)

**Desarrollo con los 8 tenis listo** (pares verde, rosa, azul y negro). Falta: el par plateado
(lo están terminando en Blender), los datos de cada ficha (proyecto, año, texto) y probar en
celulares reales.

- Los escaneos llegaron limpios y con suela reconstruida en `.blend` (zip "INVIS PROYECT"):
  extraídos en `fuentes/originales/blend/`, y las fotos de firmas en `fuentes/originales/firmas/`
  (todo fuera de git). Se convierten con `fuentes/exportar_tenis.py` (ver Herramientas).
- El recorrido se genera desde el bloque JSON `#datos-tenis` de `index.html`: portada (par 1) →
  por cada par, una parada de presentación + una por cada firma de marca → colección. Agregar un
  par o una firma es editar ese JSON; las secciones, las poses y los hotspots salen solos.
- Firmas destacadas (confirmadas por el equipo): Nescafé Dolce Gusto ("NDG powered by KRUPS",
  verde izq.), "…a la BATALLA" (verde izq.; falta el nombre de la marca), Mondelēz (verde der.),
  Bimbo y Lyncott (rosa der.), Gentera (azul izq.), Elemental (azul der.), Tec de Monterrey
  (negro der.). El negro izquierdo no tiene firma destacada. Del plateado: Coca-Cola, Heineken, Sanfer.
- Interacción: el arrastre horizontal gira el tenis que está bajo el dedo (regresa solo).
  "Explorar en 360°" muestra un tenis a la vez, con flechas, giro en 2 ejes y pellizco/rueda. En la
  colección, tocar un tenis lo abre. La ficha de marca acerca la cámara a la firma.
- Carga: el par de la portada decide cuándo se quita el cargador; los demás entran en segundo
  plano. La textura es 1K/2K/4K según el largo del tenis en píxeles (4K solo en escritorio): `nivelDeseado()`.
- Sin WebGL → rejilla con las 8 fotos fijas (`modelos/poster/`) y todo el texto.
- Probado con Chrome headless (escritorio 1440 y celular 390). **No probado en celulares reales.**

Para verlo: servir la carpeta (`fetch` del `.glb` no funciona abriendo el archivo directo):
```
"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" -m http.server 8123
```
`?debug` en la URL: en Explorar, clic sobre una firma → imprime `punto` y `normal` para el JSON.
También `tenisDebug.vista(id, giro, incl, zoom)` y `tenisDebug.puntoEn(x, y)`.
Convención: la punta de todos los tenis va hacia +Z (giro 0 = punta a la cámara); el costado
exterior del derecho es -X (giro +π/2) y el del izquierdo +X (giro -π/2).
Para revisar el recorrido conviene Chrome headless por CDP (el panel del navegador de Claude
captura a medio cuadro). Ojo: no poner `overflow:hidden` en el `<body>` para bloquear el scroll,
porque rompe el `sticky` del escenario.

**Dónde va a vivir:** la agencia lo quiere dentro de su landing, en la sección "Some of the brands
that have trusted us..." (casi al final, antes de "The transformation begins here"). Por eso todo
está en un bloque `#tenis` autocontenido: el escenario es `position: sticky` dentro de la sección y
el tono oscuro se aplica a `#tenis`, nunca al `<body>`. Anclas por sección (`#marcas`, etc.) y
`?incrustado` oculta la barra propia. GitHub Pages: https://charlycharlex.github.io/PCW-Tenis/

**Propuesta comercial** en `propuesta/`, fuera de git. Este repo es público: precios, ligas de la
propuesta y condiciones con el cliente **no se escriben aquí** (tampoco en este archivo). Equipo:
Carlos Ortega Amarillas y Diego Alvarado Mendoza.
- `propuesta/propuesta.html` es la fuente; `propuesta/exportar_vercel.py` genera el sitio estático
  en `..\PCW-Propuesta` (repo privado aparte, desplegado en Vercel).
- `propuesta/generar_mockup.py` arma `mockup.html` (el `index.html` dentro de una réplica de su landing).

### Lo que se midió en el escaneo del tenis verde

| | Original (`fuentes/originales/`) | Versión web (`modelos/tenis_verde_izq.glb`) |
|---|---|---|
| Peso | 30 MB | 0.89 MB |
| Triángulos | 858,590 | 76,963 (80k menos la limpieza de base) |
| Texturas | diffuse + normal, 8192² | solo diffuse, 2048² (el normal map no sirve con luz plana) |

- A tamaño de pantalla la versión reducida se ve casi idéntica (ver `referencias/renders/`,
  `orig_*` contra `dec_*`). Las firmas grandes se leen ("YUBAL Oloarte", "THE CHOSEN ONES");
  las pequeñas no.
- Es un Nike Dunk High x Ambush. Se ve "powered by KRUPS" en un costado (ejemplo de firma de marca).
- **Defectos del escaneo**: restos blancos de la base bajo la suela, franja blanca visible desde
  arriba, huecos dentro del cuello, falta la suela por debajo (confirmado: abajo solo hay una tapa
  plana del escaneo). Los restos de base ya se limpian solos en `optimizar_tenis.py` (caras al ras
  del piso que miran hacia arriba o son gris claro, más islas sueltas); lo poco que queda en los
  últimos ~5 mm lo recorta la página con un plano de corte (`TENIS.corteBase`) y la cámara nunca
  baja del horizonte. Pendiente a mano en Blender: cuello y suela.
- La malla viene **partida en las costuras de UV**: cualquier análisis de conectividad hay que
  hacerlo soldando vértices por posición (con aristas de bmesh cada parche parece una isla).
- La **luz viene horneada** en la textura: usar iluminación plana en la escena para no sombrear doble.

## Limitaciones técnicas identificadas

1. **Memoria de GPU en celular (la más importante).** 8 tenis × 2 texturas 2K ≈ 360 MB de VRAM →
   iOS mata la pestaña. Solución: texturas en **KTX2/Basis** (~90 MB) y tener cargados solo 2–3
   tenis a la vez. Quitar el normal map (ya hecho) deja una sola textura por tenis: ~180 MB sin KTX2,
   ~45 MB con KTX2.
2. **Legibilidad de firmas.** Propuesta: **hotspots** sobre las firmas de marcas grandes → la cámara
   se acerca, aparece logo de la marca + proyecto. Textura 4K solo bajo demanda en ese acercamiento.
3. **Conflicto scroll vs. girar en táctil.** Decisión de diseño: "modo explorar" activado con un
   toque, o giro solo con arrastre horizontal.
4. **Peso total** ~5–9 MB → cargar primero el tenis de la portada y el resto de forma diferida.
5. **No técnico:** confirmar con la agencia permiso para nombrar clientes y usar sus logos, y si
   las dedicatorias personales escritas en los tenis pueden ser públicas.

## Estimado y plan

Asumiendo escaneos listos y un desarrollador + Claude: **4–6 semanas calendario** (~3 si el diseño
viene definido). El cuello de botella suele ser diseño y escaneos, no código.

1. **Prototipo** con el tenis verde: scroll + giro 360° + un hotspot (2–3 días). Enseñarlo a la
   agencia antes de comprometer diseño.
2. **Pipeline automatizado** en Blender para los 8 tenis: limpieza, reducción, KTX2, ubicar
   hotspots (3–5 días).
3. Con la agencia: lista de firmas importantes y guion del scroll (qué tenis, qué sección, qué
   movimiento) — ~1 semana en paralelo.
4. Desarrollo completo + responsive (1.5–2 semanas).
5. Optimización y QA en celulares reales, fallback sin WebGL (~1 semana).

## Preguntas abiertas (pendientes de respuesta)

- ¿Los otros 7 tenis ya están escaneados? ¿Con qué app? ¿Mismas condiciones (escala, luz, orientación)?
- ¿La agencia trae diseño / referencia visual o lo proponemos?
- ¿Dónde vive la página: dominio propio o dentro de palmercooperwallace.com? ¿Qué plataforma usa ese sitio?
- ¿Cuáles son las marcas "grandes" a destacar?

## Herramientas en esta máquina

- **Blender 5.2**: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` — importa `.usdz`.
- `python` y `node` **no** están en el PATH; para procesar modelos usar el Python de Blender.
- `fuentes/exportar_tenis.py` — **el que se usa**: convierte un `.blend` terminado (escaneo + suela)
  en `modelos/<id>.glb` (Draco; escaneo a 100k triángulos, suela a 24k con su color horneado en los
  vértices) y `modelos/tex/<id>_1k|2k|4k.jpg`. `--girar` si la punta no viene hacia -Y de Blender.
  ```
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P fuentes\exportar_tenis.py -- fuentes\originales\blend\tenis_azul_derecho.blend azul_der [--girar]
  ```
  `fuentes/revisar_glb.py <id> <salida.jpg>` dibuja 4 vistas tal como las verá la página.
- `fuentes/optimizar_tenis.py` — (del prototipo) convierte un `.usdz` crudo en `.glb` con Draco:
  ```
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup -P fuentes\optimizar_tenis.py -- fuentes\originales\X.usdz modelos\x.glb [triangulos=80000] [textura=2048] [--renders]
  ```
  Limpia los restos de la base y omite el normal map (`--con-normal` lo conserva). Aún no comprime
  a KTX2. Si un tenis tiene suela blanca, la limpieza por color la borraría: poner `BASE_SATURACION = 0`.
- `fuentes/poster_tenis.py <id>` — foto fija del costado exterior: `modelos/poster/<id>.webp` (respaldo
  sin WebGL) y `entregables/renders/<id>.png` de 2800 px (entregable; fuera de git por su peso).

## Estructura

- `index.html` — la página (un solo archivo; three.js 0.170 por importmap + GSAP 3.12 de CDN).
- `fuentes/originales/` — escaneos `.usdz` originales (30 MB c/u, fuera de git).
- `fuentes/` — scripts de Blender.
- `modelos/` — `<id>.glb`, `tex/` (texturas del escaneo en 3 tamaños) y `poster/` (fotos fijas `.webp`).
- `referencias/renders/` — renders de comparación original vs. reducido.
