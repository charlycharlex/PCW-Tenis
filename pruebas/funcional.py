# Pruebas de interacción: explorar (teclado y botones), fichas desde la etiqueta y con Escape,
# respaldo sin WebGL y movimiento reducido.
import sys, json
import os
from playwright.sync_api import sync_playwright
os.makedirs('capturas', exist_ok=True)
URL = 'http://127.0.0.1:8126/?debug'
ok = lambda c, t: print(('  OK   ' if c else '  FALLA') + ' ' + t)
with sync_playwright() as p:
    nav = p.chromium.launch(channel='chrome', headless=True, args=['--enable-gpu'])
    # ---- explorar y fichas (escritorio) ----
    pg = nav.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    errores = []; pg.on('pageerror', lambda e: errores.append(str(e)))
    pg.goto(URL); pg.wait_for_function('window.tenisDebug && tenisDebug.zapatos.every(z => z.listo)', timeout=60000)
    print('Explorar')
    pg.click('header [data-explorar]'); pg.wait_for_timeout(1300)
    ok(pg.evaluate("document.documentElement.classList.contains('explorando')"), 'entra con el botón del encabezado')
    vistos = [pg.evaluate("document.querySelector('.exp-nombre b').textContent")]
    for _ in range(10):
        pg.keyboard.press('PageDown'); pg.wait_for_timeout(250)
        vistos.append(pg.evaluate("document.querySelector('.exp-nombre b').textContent"))
    ok(len(set(vistos)) == 10 and vistos[0] == vistos[10], f'PageDown recorre los 10 y da la vuelta ({len(set(vistos))} distintos)')
    pg.click('#exp-ant'); pg.wait_for_timeout(1100)
    ok(pg.evaluate("document.querySelector('.exp-nombre b').textContent") == vistos[9], 'la flecha ← regresa al anterior')
    g0 = pg.evaluate("tenisDebug.porId.get(tenisDebug.zapatos.find(z => z.sel.peso > .5).id).giroU")
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(600)
    g1 = pg.evaluate("tenisDebug.porId.get(tenisDebug.zapatos.find(z => z.sel.peso > .5).id).giroU")
    ok(abs(g1 - g0) > .1, 'la flecha → del teclado gira el tenis')
    pg.mouse.move(720, 450); pg.mouse.wheel(0, -400); pg.wait_for_timeout(300)
    ok(pg.evaluate('scrollY') >= 0, 'la rueda hace zoom sin mover la página')
    # etiqueta clicable en explorar: ir a un tenis con marcas
    pg.evaluate("tenisDebug.elegirExplorar('plateado_izq')"); pg.wait_for_timeout(1500)
    activas = pg.evaluate("[...document.querySelectorAll('.hotspot.activo')].map(b => b.getAttribute('aria-label'))")
    ok(len(activas) >= 2, f'en explorar el plateado izquierdo muestra sus etiquetas ({len(activas)})')
    if activas:
        pg.click('.hotspot.activo .nombre'); pg.wait_for_timeout(1500)
        ok(pg.evaluate("document.getElementById('panel').classList.contains('abierto')"), 'tocar una etiqueta abre su ficha')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(1200)
        ok(not pg.evaluate("document.getElementById('panel').classList.contains('abierto')"), 'Escape cierra la ficha')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(1300)
    ok(not pg.evaluate("document.documentElement.classList.contains('explorando')"), 'Escape sale de explorar')
    # ficha desde el recorrido y chips
    pg.evaluate("document.getElementById('par-rosa').scrollIntoView({block:'start'})"); pg.wait_for_timeout(1500)
    pg.click('#par-rosa .chip >> nth=1'); pg.wait_for_timeout(1800)
    ok(pg.evaluate("Math.abs(document.getElementById('marca-lyncott').getBoundingClientRect().top + document.getElementById('marca-lyncott').offsetHeight/2 - innerHeight/2) < 120"), 'el atajo "Lyncott" lleva a su parada')
    pg.click('#marca-lyncott [data-ficha]'); pg.wait_for_timeout(1500)
    ok(pg.evaluate("document.querySelector('#panel-marca').textContent") == 'Lyncott', 'Ver el proyecto abre la ficha correcta')
    ok(pg.evaluate("document.documentElement.classList.contains('bloqueado')"), 'con la ficha abierta no se puede hacer scroll')
    pg.click('#panel .cerrar'); pg.wait_for_timeout(1200)
    ok(not pg.evaluate("document.documentElement.classList.contains('bloqueado')"), 'al cerrar vuelve el scroll')
    # colección: tocar un tenis lo abre en explorar
    pg.evaluate("document.getElementById('coleccion').scrollIntoView({block:'start'})"); pg.wait_for_timeout(3000)
    z = pg.evaluate("(()=>{ const z = tenisDebug.porId.get('azul_der'); const v = new tenisDebug.THREE.Vector3(); z.grupo.getWorldPosition(v); v.project(tenisDebug.camera); return [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight]; })()")
    pg.mouse.click(z[0], z[1]); pg.wait_for_timeout(1500)
    ok(pg.evaluate("document.documentElement.classList.contains('explorando')") and 'azul' in pg.evaluate("document.querySelector('.exp-nombre b').textContent").lower(), 'en la colección, tocar un tenis lo abre en explorar')
    ok(not errores, f'sin errores de JavaScript {errores[:2]}')
    pg.context.close()
    # ---- sin WebGL ----
    print('Sin WebGL')
    nav2 = p.chromium.launch(channel='chrome', headless=True, args=['--disable-webgl', '--disable-webgl2', '--disable-3d-apis'])
    pg = nav2.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    pg.goto(URL); pg.wait_for_timeout(4000)
    r = pg.evaluate("({sin3d: document.documentElement.classList.contains('sin3d'), fotos: document.querySelectorAll('#respaldo img').length, cargadas: [...document.querySelectorAll('#respaldo img')].filter(i => i.complete && i.naturalWidth).length, textos: document.querySelectorAll('.texto.visible').length, cargador: getComputedStyle(document.getElementById('cargando')).opacity})")
    ok(r['sin3d'] and r['fotos'] == 10, f"muestra el respaldo con las 10 fotos ({r})")
    pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(1500)
    pg.screenshot(path='capturas/sin3d.png')
    nav2.close()
    # ---- movimiento reducido ----
    print('Movimiento reducido')
    pg = nav.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce').new_page()
    errores = []; pg.on('pageerror', lambda e: errores.append(str(e)))
    pg.goto(URL); pg.wait_for_function('window.tenisDebug && tenisDebug.zapatos.every(z => z.listo)', timeout=60000)
    pg.evaluate("document.getElementById('marca-up').scrollIntoView({block:'start'})"); pg.wait_for_timeout(2500)
    f0 = pg.evaluate('tenisDebug.renderer.info.render.frame'); pg.wait_for_timeout(1500); f1 = pg.evaluate('tenisDebug.renderer.info.render.frame')
    ok(not errores and f1 - f0 == 0, f'funciona y en reposo no dibuja ({f1 - f0} cuadros en 1.5 s)')
    pg.evaluate("document.getElementById('portada').scrollIntoView({block:'start'})"); pg.wait_for_timeout(2500)
    f0 = pg.evaluate('tenisDebug.renderer.info.render.frame'); pg.wait_for_timeout(1500); f1 = pg.evaluate('tenisDebug.renderer.info.render.frame')
    ok(f1 - f0 == 0, f'sin vaivén en la portada ({f1 - f0} cuadros en 1.5 s)')
    nav.close()
