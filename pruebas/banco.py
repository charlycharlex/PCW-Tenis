# Banco de pruebas de la landing de tenis: recorre la página con la rueda (como una persona) y mide.
#   python banco.py <perfil> [url] [--webkit] [--headed]
# perfiles: retina (1440x900 @2x), laptop (1536x864 @1.25), celular (390x844 @3, táctil)
import sys, json, time, statistics
from playwright.sync_api import sync_playwright

PERFILES = {
    'retina':  dict(viewport={'width': 1440, 'height': 900}, device_scale_factor=2),
    'laptop':  dict(viewport={'width': 1536, 'height': 864}, device_scale_factor=1.25),
    'celular': dict(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True,
                    user_agent='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0 Mobile Safari/537.36'),
}
args = [a for a in sys.argv[1:] if not a.startswith('--')]
flags = {a for a in sys.argv[1:] if a.startswith('--')}
perfil = args[0] if args else 'retina'
url = args[1] if len(args) > 1 else 'http://127.0.0.1:8126/?debug'

INIT = r"""
window.__m = {cuadros: [], loaf: [], subidas: [], marca: 0};
(function(){
  let prev = 0;
  function f(t){ if(prev) __m.cuadros.push([t, t - prev]); prev = t; requestAnimationFrame(f); }
  requestAnimationFrame(f);
  try{ new PerformanceObserver(l => { for(const e of l.getEntries()){ const fin = e.startTime + e.duration;
        __m.loaf.push({t: e.startTime, dur: e.duration,
        // antes del render (tareas), callbacks de rAF, estilo+layout+pintado hasta el final del cuadro
        tareas: Math.round((e.renderStart || fin) - e.startTime), raf: Math.round((e.styleAndLayoutStart || fin) - (e.renderStart || fin)),
        estiloPintado: Math.round(fin - (e.styleAndLayoutStart || fin)), seccion: document.querySelector('.texto.visible')?.closest('.paso')?.id,
        scripts: e.scripts.map(s => (s.sourceFunctionName || s.invoker || '?') + ':' + Math.round(s.duration))}); } })
        .observe({type: 'long-animation-frame', buffered: false}); }catch(e){}
  const espera = setInterval(()=>{
    if(!window.tenisDebug?.renderer) return;
    clearInterval(espera);
    const r = tenisDebug.renderer, orig = r.initTexture.bind(r);
    r.initTexture = (t)=>{ const w = t.image?.width, h = t.image?.height; const a = performance.now(); orig(t); __m.subidas.push([a, performance.now() - a, w + 'x' + h, t.name || '']); };
  }, 20);
})();
"""

def resumen(iv):
    if not iv: return {}
    s = sorted(iv)
    return {'cuadros': len(iv), 'mediana': round(statistics.median(iv), 1), 'p95': round(s[int(len(s) * .95)], 1),
            'max': round(s[-1], 1), '>20ms': sum(x > 20 for x in iv), '>33ms': sum(x > 33 for x in iv),
            '>50ms': sum(x > 50 for x in iv), '>100ms': sum(x > 100 for x in iv), 'jank_ms': round(sum(max(0, x - 16.7) for x in iv))}

with sync_playwright() as p:
    if '--webkit' in flags:
        nav = p.webkit.launch(headless='--headed' not in flags)
    else:
        nav = p.chromium.launch(channel='chrome', headless='--headed' not in flags,
                                args=['--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-webgpu'])
    ctx = nav.new_context(**PERFILES[perfil])
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    errores = []
    pg.on('pageerror', lambda e: errores.append(str(e)))
    pg.on('console', lambda m: m.type in ('error', 'warning') and errores.append(m.type + ': ' + m.text))
    t0 = time.time()
    pg.goto(url)
    pg.wait_for_function('window.tenis3D === true', timeout=60000)
    t_primer = round(time.time() - t0, 2)
    pg.wait_for_function('window.tenisDebug && tenisDebug.zapatos.every(z => z.listo)', timeout=90000)
    t_todos = round(time.time() - t0, 2)
    info = pg.evaluate("""()=>{ const gl = tenisDebug.renderer.getContext(); const ext = gl.getExtension('WEBGL_debug_renderer_info');
        return {gpu: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : '?', dpr: tenisDebug.renderer.getPixelRatio(),
                programas: tenisDebug.renderer.info.programs.length}; }""")
    pg.wait_for_timeout(1500)
    secciones = pg.evaluate("[...document.querySelectorAll('#recorrido .paso')].map(s => [s.id, s.getBoundingClientRect().top + scrollY])")
    pg.mouse.move(PERFILES[perfil]['viewport']['width'] / 2, PERFILES[perfil]['viewport']['height'] / 2)
    inicio = pg.evaluate('performance.now()')
    por_seccion = []
    for sid, top in secciones[1:]:
        a = pg.evaluate('performance.now()')
        prog0 = pg.evaluate('tenisDebug.renderer.info.programs.length')
        y = pg.evaluate('scrollY')
        while y < top - 5:
            pg.mouse.wheel(0, min(100, top - y))
            pg.wait_for_timeout(40)
            y2 = pg.evaluate('scrollY')
            if y2 == y: break
            y = y2
        pg.wait_for_timeout(900)          # alguien leyendo
        b = pg.evaluate('performance.now()')
        iv = pg.evaluate(f'__m.cuadros.filter(c => c[0] >= {a} && c[0] < {b}).map(c => c[1])')
        sub = pg.evaluate(f'__m.subidas.filter(s => s[0] >= {a} && s[0] < {b}).map(s => Math.round(s[1]))')
        por_seccion.append({'seccion': sid, 'max_ms': round(max(iv), 1) if iv else None, '>33ms': sum(x > 33 for x in iv),
                            'subidas_ms': sub, 'programas_nuevos': pg.evaluate('tenisDebug.renderer.info.programs.length') - prog0})
    fin = pg.evaluate('performance.now()')
    iv = pg.evaluate(f'__m.cuadros.filter(c => c[0] >= {inicio} && c[0] < {fin}).map(c => c[1])')
    loaf = pg.evaluate(f'__m.loaf.filter(e => e.t >= {inicio} && e.dur > 50).sort((a,b) => b.dur - a.dur).slice(0, 8)')
    subidas = pg.evaluate(f'__m.subidas.filter(s => s[0] >= {inicio}).map(s => Math.round(s[1]))')
    subidas_det = pg.evaluate(f'__m.subidas.filter(s => s[0] >= {inicio}).map(s => [Math.round(s[1]), s[2], document.querySelector(".texto.visible")?.closest(".paso")?.id])')
    mem = pg.evaluate('({...tenisDebug.renderer.info.memory, programas: tenisDebug.renderer.info.programs.length})')
    salida = {'perfil': perfil, 'motor': 'webkit' if '--webkit' in flags else 'chrome', **info,
              'carga_primer_par_s': t_primer, 'carga_todos_s': t_todos, 'recorrido': resumen(iv),
              'subidas_textura_ms': subidas, 'subidas_detalle': subidas_det, 'dpr_final': pg.evaluate('tenisDebug.renderer.getPixelRatio()'), 'memoria_final': mem,
              'peores_secciones': sorted(por_seccion, key=lambda s: -(s['max_ms'] or 0))[:8],
              'cuadros_largos': [{k: (round(v) if isinstance(v, float) else v) for k, v in e.items() if k != 't'} for e in loaf],
              'errores': errores[:10], 'recursos_404': pg.evaluate("performance.getEntriesByType('resource').filter(e => e.responseStatus === 404).map(e => e.name)")}
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    nav.close()
