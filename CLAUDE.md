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

## Estado actual (2026-09-23)

**Prototipo con el tenis verde listo** (paso 1 del plan): `index.html`, falta enseñarlo a la agencia.

- Recorrido de 5 secciones con scroll (GSAP ScrollTrigger interpolando poses del tenis): portada →
  el ritual → las marcas (acercamiento a KRUPS, fondo marino) → gíralo → cierre.
- Giro: en el recorrido, arrastre **horizontal** (en táctil el vertical sigue siendo scroll,
  `touch-action: pan-y`) y el tenis regresa solo a su pose; en la sección "Gíralo" el giro se queda.
  "Explorar en 360°" abre un modo aparte: giro en dos ejes, pellizco/rueda para acercar, scroll bloqueado.
  Se implementaron **las dos** opciones de la limitación 3 para que la agencia elija.
- Un hotspot (KRUPS): anillo + etiqueta; al tocarlo la cámara se acerca a la firma y abre un panel
  con datos **de ejemplo** (proyecto y año inventados, marcado en el propio panel).
- Colores y tipografía (Manrope) tomados de palmercooperwallace.com. Textos provisionales.
- Sin WebGL / sin CDN / error de carga → foto fija (`modelos/tenis_verde_izq.webp`) y el texto completo.
- Probado en el navegador de Claude a 800, 1440 y 375 px. **No probado en celulares reales.**

Para verlo: servir la carpeta (`fetch` del `.glb` no funciona abriendo el archivo directo):
```
"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" -m http.server 8123
```
`?debug` en la URL: clic sobre el tenis → imprime en consola `punto` y `normal` para un hotspot
nuevo (se pegan en `HOTSPOTS`). Las poses del scroll están en `poses()`; `giro 0` = talón a la cámara.

**Dónde va a vivir:** la agencia lo quiere dentro de su landing, en la sección "Some of the brands
that have trusted us..." (casi al final, antes de "The transformation begins here"). Por eso todo
está en un bloque `#tenis` autocontenido: el escenario es `position: sticky` dentro de la sección y
el tono oscuro se aplica a `#tenis`, nunca al `<body>`. Anclas por sección (`#marcas`, etc.) y
`?incrustado` oculta la barra propia. GitHub Pages: https://charlycharlex.github.io/PCW-Tenis/

**Propuesta comercial** en `propuesta/` (fuera de git: trae precios y el repo es público). Está
publicada como artifact: https://claude.ai/artifact/NwxXanXRhwn5ScRawzjV2K — $4,000 MXN + una sesión
de asesoría de marca, entrega 6 nov 2026. Equipo: Carlos Ortega Amarillas y Diego Alvarado Mendoza.
`propuesta/generar_mockup.py` arma `mockup.html` (el `index.html` dentro de una réplica de su landing).

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
- `fuentes/optimizar_tenis.py` — convierte un `.usdz` en `.glb` con Draco:
  ```
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup -P fuentes\optimizar_tenis.py -- fuentes\originales\X.usdz modelos\x.glb [triangulos=80000] [textura=2048] [--renders]
  ```
  Limpia los restos de la base y omite el normal map (`--con-normal` lo conserva). Aún no comprime
  a KTX2. Si un tenis tiene suela blanca, la limpieza por color la borraría: poner `BASE_SATURACION = 0`.
- `fuentes/poster_tenis.py` — imagen fija `.webp` para el respaldo sin WebGL:
  `blender.exe -b --factory-startup -P fuentes\poster_tenis.py -- modelos\x.glb modelos\x.webp [giro_grados]`

## Estructura

- `index.html` — la página (un solo archivo; three.js 0.170 por importmap + GSAP 3.12 de CDN).
- `fuentes/originales/` — escaneos `.usdz` originales (30 MB c/u, fuera de git).
- `fuentes/` — scripts de Blender.
- `modelos/` — `.glb` optimizados que usa la página y su póster `.webp`.
- `referencias/renders/` — renders de comparación original vs. reducido.
