# Recorre la página y reporta si en alguna parada la página queda más ancha que la pantalla, y qué elementos
# se salen por la derecha (eso crea scroll horizontal; los que se salen por la izquierda no).
import sys
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8126/?debug'
J = """()=>{ const d = document.documentElement; const fuera = [];
  for(const el of document.querySelectorAll('body *')){ const r = el.getBoundingClientRect(); if(r.width && r.right > d.clientWidth + 1)
    fuera.push((el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + [...el.classList].join('.')) + (el.closest('.hotspot') ? '(' + el.closest('.hotspot').getAttribute('aria-label').replace('Ver el proyecto con ', '') + ')' : '') + ' →' + Math.round(r.right)); }
  return {scrollW: d.scrollWidth, clientW: d.clientWidth, fuera: fuera.slice(0, 5)}; }"""
PERF = {'celular': dict(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True),
        'escritorio': dict(viewport={'width': 1440, 'height': 900})}
with sync_playwright() as p:
    nav = p.chromium.launch(channel='chrome', headless=True, args=['--enable-gpu'])
    for nombre, vp in PERF.items():
        pg = nav.new_context(**vp).new_page()
        pg.goto(url); pg.wait_for_function('window.tenisDebug && tenisDebug.zapatos.every(z => z.listo)', timeout=60000); pg.wait_for_timeout(1500)
        secciones = pg.evaluate("[...document.querySelectorAll('#recorrido .paso')].map(s => [s.id, s.getBoundingClientRect().top + scrollY])")
        malas = 0
        for sid, top in secciones:
            y = pg.evaluate('scrollY')
            while y < top - 5:
                pg.evaluate(f'scrollBy(0, {min(100, top - y)})'); pg.wait_for_timeout(25)
                y2 = pg.evaluate('scrollY')
                if y2 == y: break
                y = y2
            pg.wait_for_timeout(700)
            r = pg.evaluate(J)
            if r['scrollW'] > r['clientW']:
                malas += 1
                if malas <= 3: print(f"  {nombre} {sid:<16} ancho de página {r['scrollW']} en pantalla de {r['clientW']}: {r['fuera']}")
        print(f"{nombre}: paradas con la página más ancha que la pantalla = {malas} de {len(secciones)}")
        pg.context.close()
    nav.close()
