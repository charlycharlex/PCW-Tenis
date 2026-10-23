# PCW Tenis — landing con los tenis firmados

## El proyecto

Landing para **Palmer Cooper Wallace** (agencia de marketing, https://palmercooperwallace.com/).
Cada vez que la agencia termina un proyecto, el cliente les firma unos tenis. La landing muestra
esos tenis en 3D como una forma innovadora de enseñar con qué marcas han trabajado.

- **5 pares = 10 tenis**, escaneados en 3D (fotogrametría). Orden del recorrido (pedido por el
  equipo): **verde, rosa, azul, plateado, negro**.
- Solo importan las firmas de **las marcas grandes** (14, ver abajo); el resto de mensajes es textura.
- Referencia de interacción: https://www.eathungrytiger.com/ — el objeto 3D se anima conforme
  se hace scroll; además se puede **girar cada tenis 360°**.

Precedente propio: la landing de EzEat (`C:\Users\charl\Documents\Landingezeat`), mismo stack.

## Estado actual (2026-10-23)

**Los 10 tenis listos, auditoría de rendimiento hecha y verificada.** Publicado en GitHub Pages
(https://charlycharlex.github.io/PCW-Tenis/) solo cuando el equipo lo pide: el repo es público.

Pendiente:
- Los datos de cada ficha (proyecto, año, texto): hoy sale "Datos de ejemplo…". Lo pasa la agencia.
- Decidir si UP se marca también en el plateado (en la suela del izquierdo firma "Cecilia /UP/").
- Probar en celulares reales, sobre todo un iPhone (todo lo demás se probó en Chrome y WebKit
  automatizados, ver Pruebas).
- Confirmar con la agencia el permiso para nombrar clientes y mostrar las dedicatorias.

### Datos y recorrido
- Todo sale del bloque JSON `#datos-tenis` de `index.html`: portada (= par 1) → por cada par, una
  parada de presentación + una por cada firma de marca → colección. Cambiar el orden, agregar un par
  o una firma es editar ese JSON; secciones, numeración ("Firma N de 14"), poses, hotspots, colección
  y modo explorar salen solos. **Si cambia el primer par, cambiar también las precargas del `<head>`.**
- Firmas destacadas (14): Nescafé Dolce Gusto y Lucha Libre (verde izq.), Mondelēz y Santa Clara
  (verde der.), Bimbo, Lyncott y Tequila Altos (rosa der.), Gentera y UP (azul izq.), Elemental (azul
  der.), Coca-Cola, Sanfer y Heineken (plateado izq.), Tec de Monterrey (negro der.). Sin firma
  destacada: rosa izq., negro izq., plateado der.
- Interacción: el arrastre horizontal gira el tenis bajo el dedo (regresa solo). "Explorar en 360°":
  un tenis a la vez, flechas/PageUp/PageDown, giro en 2 ejes, pellizco/rueda. En la colección, tocar
  un tenis lo abre en explorar. La ficha acerca la cámara a la firma (y ahí sí usa 4K).
- La cámara nunca baja del horizonte (`inclFrente` ≥ .02, en explorar `inclUsuario` ≥ -.12): ningún
  escaneo tiene una cara de abajo presentable.
- Medición opcional: abrir ficha/explorar dispara `tenis:ficha` / `tenis:explorar` en `document` y,
  si existe, `dataLayer.push({event: 'tenis_ficha', marca, …})` (Google Tag Manager / GA4).

### Rendimiento (lo que hace la página y por qué)
Medido con las herramientas de `pruebas/` en la laptop del equipo (Radeon integrada, D3D11).
- **Subir una textura a la GPU congela la página mientras dura**: JPEG 2K 15–60 ms, 4K 100–280 ms.
  Por eso 1K y 2K van en **KTX2** (Basis ETC1S, `modelos/tex/*.ktx2`): suben en < 1 ms, ocupan 4–8×
  menos memoria de video y las transcodifica un worker. La 4K sigue en JPEG (el codificador no acepta
  16 Mpx) y **solo se usa con la ficha abierta o en explorar**, y se sube con la escena quieta.
  Si un KTX2 falla, se usa el JPEG del mismo nivel (los JPEG siguen en el repo).
- Texturas por capa (`''` escaneo, `'_firmas'` suela del plateado izq.) y nivel; caché con
  presupuesto en bytes (`PRESUPUESTO`): las grandes se quedan mientras quepan y se suelta la que lleva
  más tiempo sin usarse; la 1K de cada tenis no se suelta nunca. Sección 4 de `index.html`.
- Todos los tenis aparecen con la 1K y suben de nivel solos (`nivelDeseado`).
- Solo dibuja si algo cambió (una "huella" de las poses) y nada con la sección fuera de pantalla.
  Resolución adaptable (baja sola si los cuadros tardan); sin MSAA con densidad ≥ 2.
- Los shaders se compilan al cargar cada tenis (`compileAsync`), no al aparecer.
- Carga diferida: dentro de la landing de la agencia no baja nada hasta que el visitante está a
  pantalla y media de la sección. Los tenis de fondo se piden cuando el navegador está libre.
- Todo desde `vendor/` (three r170 minificado, cargadores, Draco, Basis, GSAP, fuentes): un solo
  origen. `<link rel="preload">` del primer par en el `<head>` (la 2K solo donde seguro se usa).
- Detalles que costaban cuadros: la firma se "escribe" con dos transform que se cancelan (antes
  clip-path, que repintaba cada cuadro); el latido del anillo solo en la etiqueta visible (antes las
  14 recalculaban estilos 60 veces por segundo con la página quieta); las etiquetas escriben al DOM
  solo lo que cambió; sin `backdrop-filter` en táctiles.

Resultado contra la versión publicada el 2026-10-23 (`d510fd8`): ver `pruebas/` y el historial de git
(cada commit trae sus números). En retina, peor cuadro al hacer scroll 600 → ~80 ms y tirón acumulado
2.2 s → ~0.35 s; primer par visible en escritorio con 4G 7.6 → 5.5 s.

Decisiones de **no** hacer, con su porqué:
- Bajar los escaneos de 100k a 50k triángulos: decimar el `.glb` abre grietas en las costuras de UV
  (la malla viene partida ahí), y re-exportar desde los `.blend` cambia más cosas (ver Herramientas).
  La GPU tarda ~1.7 ms en dibujar la colección completa en la laptop: no hace falta.
- `powerPreference: 'high-performance'` se queda: como no dibuja en reposo, la GPU potente casi no
  trabaja, y en laptops con dos GPU la animación va mejor con ella.
- `scrub` del recorrido (.9 s) no se tocó: los tirones eran las texturas, no eso. Es cuestión de gusto.

### Errores ya corregidos (que no regresen: los revisan `pruebas/tono.py` y `pruebas/ancho.py`)
- **Tono**: 9 de las 14 paradas de marca salían en claro (dos paradas oscuras seguidas se traslapan;
  la que terminaba quitaba el tono). Ahora es oscuro si cualquier sección oscura está activa.
- **Ancho**: las etiquetas invisibles se quedaban fuera de la pantalla al salir su tenis y ensanchaban
  la página (scroll horizontal; en celular el encabezado se desacomodaba). `#hotspots` recorta.
- **Barra de scroll**: al abrir ficha/explorar en Windows la página se ensanchaba 15 px
  (`scrollbar-gutter: stable`).

### Plateado (llegó como `.blend`, distinto a los otros 8)
Las 3 marcas están en el **izquierdo**: Coca-Cola (punta), Sanfer (costado exterior) y Heineken (en la
**suela**, cerca del talón). Lo resuelto en `exportar_tenis.py`: punta hacia +X (`--giro=-90`); la suela
trae firmas reproyectadas en un atlas 8192×2048 → malla aparte `firmas` con su textura
(`tex/<id>_firmas_*`) × luz horneada en vértices; sus piezas usan UV con nombres distintos (se
renombran antes de unir, si no quedan en (0,0)); cuerpo cromado (ORM: azul = metal) → `tex/<id>_metal.jpg`
y la página suma reflejos de un entorno dibujado en canvas solo donde hay metal (`reflectivity` .28);
los parches metálicos se hornean con metallic=0; un plano "Fondo" visible en render ensuciaba el horneado.

## Integración en la landing de la agencia
Va en la sección "Some of the brands that have trusted us..." (casi al final). Se copian: el bloque
`#tenis`, `#panel`, `#explorar-ui`, el JSON `#datos-tenis`, los `<script>` y las carpetas `vendor/` y
`modelos/`. El tono oscuro se aplica a `#tenis`, nunca al `<body>`; `?incrustado` oculta la barra propia.
- **No copiar los `<link rel="preload">`/`modulepreload` del `<head>`** (romperían la carga diferida).
- El `importmap` tiene que ir antes de cualquier `modulepreload` o `<script type="module">`.
- No poner `overflow:hidden` en un ancestro del escenario (rompe el `sticky`); el bloqueo de scroll va
  en `<html>`.
- Si su sitio tiene Content-Security-Policy (probado con cada variante, ver `pruebas/`):
  - `script-src 'self' 'wasm-unsafe-eval'` y `worker-src 'self' blob:` son **necesarios**: Draco es
    WebAssembly y corre en workers creados desde blob:. Sin ellos la página lo detecta al arrancar y
    muestra el respaldo con fotos (antes se quedaba en el cargador para siempre).
  - `'unsafe-eval'` en `script-src` es **opcional**: el transcodificador de Basis (KTX2) genera
    funciones con `new Function`. Sin él la página usa los JPEG en todos los niveles; se ve igual.
  - `connect-src 'self'`, `font-src 'self'`, `img-src 'self' data: blob:`. Ningún dominio externo.
  - Los `<script>` (también el `importmap`; el JSON de datos no, porque no se ejecuta) y el `<style>`
    van en línea: con CSP estricta necesitan `nonce` (o `'unsafe-inline'`), o sacarlos a archivos.
- `propuesta/generar_mockup.py` arma `propuesta/mockup.html` (réplica de su landing con la sección
  dentro; quita las precargas y ajusta rutas). `propuesta/` está fuera de git: este repo es público y
  ahí van precios y condiciones (**no escribirlos aquí**). Equipo: Carlos Ortega Amarillas y Diego
  Alvarado Mendoza.

## Para verlo
Servir la carpeta (abrir el archivo directo no funciona: `fetch` de los modelos):
```
python pruebas\servidor_gzip.py . 8126        (comprime como GitHub Pages)
"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" -m http.server 8123
```
`?debug`: en Explorar, clic sobre una firma → imprime `punto` y `normal` para el JSON (por eso en debug
tocar un tenis de la colección no lo abre). `tenisDebug.vista(id, giro, incl, zoom)`, `puntoEn(x, y)`,
`renderer.info.render.frame` (cuadros dibujados). Convención: la punta de todos va hacia +Z (giro 0 =
punta a la cámara); el costado exterior del derecho es -X (giro +π/2), el del izquierdo +X (-π/2).

## Pruebas (`pruebas/`)
Chrome y WebKit automatizados con Playwright (usa el Chrome instalado; WebKit se baja aparte):
```
python -m venv .venv && .venv\Scripts\pip install playwright pillow
.venv\Scripts\python -m playwright install webkit        (solo para --webkit)
```
Con la página servida en 8126 (`servidor_gzip.py`):
- `banco.py <retina|laptop|celular> [url] [--webkit]` — recorre con la rueda como una persona y mide
  cada cuadro, cuadros largos (con atribución), subidas de textura y shaders compilados.
- `tono.py`, `ancho.py` — tono correcto en cada parada; página nunca más ancha que la pantalla.
- `funcional.py` — explorar, fichas, Escape, atajos, colección, sin WebGL, movimiento reducido.
- `hoja.py <laptop|celular> salida.png` — captura de las 20 paradas en una hoja.
- `carga.py [n] [perfil] [url_antes] [url_ahora]` — carga en frío con 4G simulado.
- `csp.py` — la página bajo 4 Content-Security-Policy distintas (levanta sus propios servidores).
Ojo al leer números: Chrome sin ventana mete 2–3 tirones de ~240 ms por recorrido que también tiene
una página de control con un solo cubo (son del entorno, no de la página). Comparar siempre A/B en
el mismo lote y con medianas de varias corridas. El panel del navegador de Claude se pausa solo y no
sirve para medir.

## Herramientas
- **Blender 5.2**: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`. **Node 24** y
  **Python 3.13** están en el PATH (`python` a secas puede abrir la tienda de Windows: usar la ruta
  `%LOCALAPPDATA%\Programs\Python\Python313\python.exe` o `py`).
- `fuentes/exportar_tenis.py` — convierte un `.blend` terminado en `modelos/<id>.glb` (Draco; escaneo
  100k triángulos, suela 24k con color horneado en vértices, suela con firmas 30k) y
  `modelos/tex/<id>_1k|2k|4k.jpg` (+ `_firmas_*`, `_metal` si aplican). `--girar` (180°) o
  `--giro=<grados>` si la punta no viene hacia -Y de Blender.
  ```
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P fuentes\exportar_tenis.py -- fuentes\originales\blend\tenis_plateado_izquierdo.blend plateado_izq --giro=-90
  ```
  **Ojo:** el exportador cambió para el plateado y ya no reproduce exactamente a los 8 primeros (por
  ejemplo, en el verde detecta una pieza de suela con imagen propia y la separa como "firmas", y el verde
  necesitaba `--girar`, que no quedó registrado). No re-exportarlos sin revisar uno por uno orientación,
  hotspots y aspecto.
- `fuentes/ktx2/codificar.mjs` — pasa las texturas 1K/2K a KTX2 (las que falten o estén viejas):
  `cd fuentes\ktx2 && npm install --ignore-scripts && node codificar.mjs [id]`. Hay que correrlo
  después de exportar un tenis.
- `fuentes/revisar_glb.py <id> <salida.jpg>` — 4 vistas tal como las dibuja la página.
- `fuentes/firma_desde_uv.py <id> escaneo|firmas <u> <v>` — ubica una firma sin abrir la página (px
  de la 4K → u = x/ancho, v = 1 - y/alto) y da `punto`/`normal` para el JSON.
- `fuentes/poster_tenis.py <id>` — foto fija para el respaldo sin WebGL (`modelos/poster/<id>.webp`) y
  render de 2800 px (`entregables/renders/`, fuera de git).
- `fuentes/optimizar_tenis.py` — (del prototipo) `.usdz` crudo → `.glb`.

## Estructura
- `index.html` — la página (un solo archivo).
- `vendor/` — librerías y fuentes servidas desde el sitio (versiones y licencias en `vendor/LEEME.txt`).
- `modelos/` — `<id>.glb`, `tex/` (KTX2 1K/2K, JPEG 1K/2K/4K, máscaras de metal), `poster/` (`.webp`).
- `fuentes/` — scripts de Blender y `ktx2/`; `fuentes/originales/` (escaneos y `.blend`, fuera de git).
- `pruebas/` — herramientas de medición y verificación (sus capturas y medidas, fuera de git).
- `referencias/renders/` — comparación del prototipo (escaneo original contra reducido).

## Historia breve
Prototipo con un solo `.usdz` (tenis verde): 30 MB / 858k triángulos / texturas 8K → 0.9 MB / ~80k /
2K, sin diferencia visible a tamaño de pantalla. La luz viene horneada en la textura (por eso se dibuja
sin luces) y la malla viene partida en las costuras de UV (para analizar conectividad hay que soldar
vértices por posición). Los 8 primeros llegaron después como `.blend` limpios con la suela reconstruida.
