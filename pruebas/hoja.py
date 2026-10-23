# Hoja de contactos: recorre todas las paradas con la rueda y arma una cuadrícula con una captura de
# cada una (más el tono y el nivel de textura), para revisar todo de un vistazo.
#   python hoja.py <laptop|celular> <salida.png> [url]
import sys, math
import os
from playwright.sync_api import sync_playwright
os.makedirs('capturas', exist_ok=True)
from PIL import Image, ImageDraw
perfil, salida = sys.argv[1], sys.argv[2]
url = sys.argv[3] if len(sys.argv) > 3 else 'http://127.0.0.1:8126/?debug'
VP = {'laptop': dict(viewport={'width': 1536, 'height': 864}, device_scale_factor=1),
      'celular': dict(viewport={'width': 390, 'height': 844}, device_scale_factor=1, is_mobile=True, has_touch=True)}[perfil]
tomas = []
with sync_playwright() as p:
    nav = p.chromium.launch(channel='chrome', headless=True, args=['--enable-gpu'])
    pg = nav.new_context(**VP).new_page()
    errores = []; pg.on('pageerror', lambda e: errores.append(str(e)))
    pg.on('console', lambda m: m.type in ('error', 'warning') and errores.append(m.text[:120]))
    pg.goto(url); pg.wait_for_function('window.tenisDebug && tenisDebug.zapatos.every(z => z.listo)', timeout=90000)
    pg.wait_for_timeout(2500)
    secciones = pg.evaluate("[...document.querySelectorAll('#recorrido .paso')].map(s => [s.id, s.getBoundingClientRect().top + scrollY])")
    pg.mouse.move(VP['viewport']['width'] / 2, VP['viewport']['height'] / 2)
    for i, (sid, top) in enumerate(secciones):
        y = pg.evaluate('scrollY')
        while y < top - 5:
            if VP.get('has_touch'): pg.evaluate(f'scrollBy(0, {min(100, top - y)})')
            else: pg.mouse.wheel(0, min(100, top - y))
            pg.wait_for_timeout(35)
            y2 = pg.evaluate('scrollY')
            if y2 == y: break
            y = y2
        pg.wait_for_timeout(2200)
        f = f'capturas/hoja_{perfil}_{i:02d}.png'; pg.screenshot(path=f)
        info = pg.evaluate("[document.getElementById('tenis').classList.contains('tono-oscuro') ? 'oscuro' : 'claro', tenisDebug.zapatos.filter(z => z.grupo.visible).map(z => z.nivel).join(',')]")
        tomas.append((f, sid, info))
    nav.close()
cols = 5 if perfil == 'laptop' else 7
esc = .3 if perfil == 'laptop' else .42
w0, h0 = Image.open(tomas[0][0]).size
w, h = int(w0 * esc), int(h0 * esc)
filas = math.ceil(len(tomas) / cols)
hoja = Image.new('RGB', (cols * (w + 6), filas * (h + 26)), 'white')
for i, (f, sid, (tono, niveles)) in enumerate(tomas):
    x, y = (i % cols) * (w + 6), (i // cols) * (h + 26)
    hoja.paste(Image.open(f).resize((w, h)), (x, y + 22))
    ImageDraw.Draw(hoja).text((x + 2, y + 4), f'{sid} [{tono}] {niveles}', fill='black')
hoja.save(salida); print('ok', hoja.size, 'errores:', errores)
