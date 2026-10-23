# Recorre con la rueda y anota si cada parada quedó con el tono que le toca.
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8126/?debug'
with sync_playwright() as p:
    nav = p.chromium.launch(channel='chrome', headless=True, args=['--enable-gpu'])
    pg = nav.new_context(viewport={'width': 1536, 'height': 864}).new_page()
    pg.goto(url); pg.wait_for_function('window.tenis3D === true', timeout=60000); pg.wait_for_timeout(1000)
    secciones = pg.evaluate("[...document.querySelectorAll('#recorrido .paso')].map(s => [s.id, s.dataset.tono === 'oscuro', s.getBoundingClientRect().top + scrollY])")
    pg.mouse.move(700, 400); malos = []
    for sid, oscuro, top in secciones[1:]:
        y = pg.evaluate('scrollY')
        while y < top - 5:
            pg.mouse.wheel(0, min(100, top - y)); pg.wait_for_timeout(40)
            y2 = pg.evaluate('scrollY')
            if y2 == y: break
            y = y2
        pg.wait_for_timeout(700)
        real = pg.evaluate("document.getElementById('tenis').classList.contains('tono-oscuro')")
        if real != oscuro: malos.append(sid)
        print(f"{sid:<18} debe {'oscuro' if oscuro else 'claro ':<6}  quedó {'oscuro' if real else 'claro'}  {'' if real == oscuro else '  <-- MAL'}")
    print('paradas con el tono equivocado:', len(malos))
    nav.close()
