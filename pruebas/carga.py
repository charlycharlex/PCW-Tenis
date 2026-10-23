# Carga en frío con red de 4G simulada: primer pintado, primer par listo, todos listos, orígenes y duplicados.
#   python carga.py [n=3] [perfil=laptop] [url_antes] [url_ahora]
# Compara dos versiones servidas con servidor_gzip.py (por omisión: 8127 = antes, 8126 = ahora).
import sys, statistics, collections, json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
perfil = sys.argv[2] if len(sys.argv) > 2 else 'laptop'
VP = {'laptop': dict(viewport={'width': 1536, 'height': 864}, device_scale_factor=1.25),
      'celular': dict(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True)}[perfil]
URLS = {'antes': sys.argv[3] if len(sys.argv) > 3 else 'http://127.0.0.1:8127/?debug',
        'ahora': sys.argv[4] if len(sys.argv) > 4 else 'http://127.0.0.1:8126/?debug'}
res = {k: [] for k in URLS}
with sync_playwright() as p:
    nav = p.chromium.launch(channel='chrome', headless=True, args=['--enable-gpu'])
    for i in range(n):
        for k, url in URLS.items():
            ctx = nav.new_context(**VP); pg = ctx.new_page()
            cdp = ctx.new_cdp_session(pg)
            cdp.send('Network.enable'); cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
            cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 100, 'downloadThroughput': 4e6 / 8, 'uploadThroughput': 1.5e6 / 8})
            pedidas, avisos = [], []
            pg.on('request', lambda r: pedidas.append(r.url))
            pg.on('console', lambda m: m.type in ('warning', 'error') and avisos.append(m.text[:140]))
            pg.goto(url)
            pg.wait_for_function('window.tenis3D === true', timeout=120000)
            t = pg.evaluate("""()=>({fcp: performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
                                     listo: performance.now()})""")
            pg.wait_for_function('window.tenisDebug && tenisDebug.zapatos.every(z => z.listo)', timeout=180000)
            todos = pg.evaluate('performance.now()')
            pg.wait_for_timeout(3500)   # para ver avisos de precargas no usadas
            origenes = collections.Counter(urlparse(u).netloc for u in pedidas)
            dup = [u.split('/')[-1] for u, c in collections.Counter(pedidas).items() if c > 1]
            fila = {'fcp_s': round(t['fcp'] / 1000, 2), 'primer_par_s': round(t['listo'] / 1000, 2), 'todos_s': round(todos / 1000, 2),
                    'pedidos': len(pedidas), 'origenes': dict(origenes), 'duplicados': dup, 'avisos': avisos[:4]}
            res[k].append(fila)
            print(k, i, json.dumps(fila, ensure_ascii=False), flush=True)
            ctx.close()
    nav.close()
print('\nMEDIANAS:')
for k, filas in res.items():
    print(f"  {k:<6} primer pintado {statistics.median(f['fcp_s'] for f in filas)} s   primer par listo {statistics.median(f['primer_par_s'] for f in filas)} s   "
          f"los 10 listos {statistics.median(f['todos_s'] for f in filas)} s")
