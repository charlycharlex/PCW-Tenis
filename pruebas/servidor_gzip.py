# Servidor estático que comprime con gzip lo mismo que GitHub Pages (html, js, css, json, wasm, glb, svg).
#   python servidor_gzip.py <carpeta> <puerto>
import sys, os, gzip, http.server, functools
CARPETA, PUERTO = sys.argv[1], int(sys.argv[2])
COMPRIMIR = {'.html', '.js', '.mjs', '.css', '.json', '.wasm', '.glb', '.svg', '.txt'}
TIPOS = {'.wasm': 'application/wasm', '.glb': 'model/gltf-binary', '.ktx2': 'image/ktx2', '.mjs': 'text/javascript', '.js': 'text/javascript'}
cache = {}
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def guess_type(self, path):
        return TIPOS.get(os.path.splitext(path)[1].lower()) or super().guess_type(path)
    def send_head(self):
        ruta = self.translate_path(self.path.split('?')[0])
        if os.path.isdir(ruta): ruta = os.path.join(ruta, 'index.html')
        ext = os.path.splitext(ruta)[1].lower()
        if ext in COMPRIMIR and 'gzip' in self.headers.get('Accept-Encoding', '') and os.path.isfile(ruta):
            clave = (ruta, os.path.getmtime(ruta))
            if clave not in cache: cache[clave] = gzip.compress(open(ruta, 'rb').read(), 6)
            datos = cache[clave]
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(ruta)); self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Length', str(len(datos))); self.send_header('Cache-Control', 'max-age=600')
            self.end_headers()
            import io; return io.BytesIO(datos)
        return super().send_head()
http.server.ThreadingHTTPServer(('127.0.0.1', PUERTO), functools.partial(H, directory=CARPETA)).serve_forever()
