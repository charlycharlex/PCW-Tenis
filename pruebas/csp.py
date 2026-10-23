# La página bajo distintas Content-Security-Policy (como podría tenerla el sitio de la agencia).
# Levanta sus propios servidores (puertos 8140-8143) sirviendo la carpeta del proyecto.
#   python csp.py
# Lo esperado: con todo permitido, 3D con KTX2; sin 'unsafe-eval', 3D con JPEG; sin 'wasm-unsafe-eval' o
# sin workers desde blob:, el respaldo con fotos (nunca el cargador colgado).
import os, threading, functools, http.server
from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; "
CASOS = [
    (8140, 'todo permitido', BASE + "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' 'unsafe-eval'; worker-src 'self' blob:", ('3d', True)),
    (8141, "sin 'unsafe-eval'", BASE + "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; worker-src 'self' blob:", ('3d', False)),
    (8142, "sin 'wasm-unsafe-eval'", BASE + "script-src 'self' 'unsafe-inline'; worker-src 'self' blob:", ('respaldo', None)),
    (8143, 'sin workers desde blob:', BASE + "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' 'unsafe-eval'; worker-src 'self'", ('respaldo', None)),
]

def servidor(puerto, csp):
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def end_headers(self):
            if self.path.split('?')[0] in ('/', '/index.html'): self.send_header('Content-Security-Policy', csp)
            super().end_headers()
        def guess_type(self, p):
            return {'.wasm': 'application/wasm', '.js': 'text/javascript'}.get(os.path.splitext(p)[1]) or super().guess_type(p)
    s = http.server.ThreadingHTTPServer(('127.0.0.1', puerto), functools.partial(H, directory=RAIZ))
    threading.Thread(target=s.serve_forever, daemon=True).start()

for puerto, _, csp, _ in CASOS: servidor(puerto, csp)
fallas = 0
with sync_playwright() as p:
    nav = p.chromium.launch(channel='chrome', headless=True, args=['--enable-gpu'])
    for puerto, nombre, _, (espera, ktx2) in CASOS:
        ctx = nav.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page()
        pg.goto(f'http://127.0.0.1:{puerto}/?debug'); pg.wait_for_timeout(9000)
        r = pg.evaluate("""({tres: !!window.tenis3D, respaldo: document.documentElement.classList.contains('sin3d'),
            listos: window.tenisDebug ? tenisDebug.zapatos.filter(z => z.listo).length : 0,
            ktx2: window.tenisDebug ? tenisDebug.zapatos.filter(z => z.listo && z.mat.map.isCompressedTexture).length : 0,
            colgado: !document.getElementById('cargando').classList.contains('oculto')})""")
        if espera == '3d': bien = r['tres'] and r['listos'] == 10 and (r['ktx2'] == 10) == ktx2
        else: bien = r['respaldo'] and not r['colgado']
        fallas += not bien
        print(('  OK    ' if bien else '  FALLA ') + f'{nombre:<26} {r}')
        ctx.close()
    nav.close()
print('todo bien' if not fallas else f'{fallas} fallas')
