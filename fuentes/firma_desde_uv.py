# Ubica una firma en 3D a partir de dónde está en la textura: imprime "punto" y "normal" listos para
# el JSON #datos-tenis de index.html (las mismas coordenadas que da ?debug al hacer clic en la página).
#
# Uso:
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup -P fuentes\firma_desde_uv.py -- ^
#       <id> <malla> <u> <v> [<u> <v> ...]
#   <malla>: escaneo (textura tex/<id>_4k.jpg) o firmas (suela con firmas, tex/<id>_firmas_4k.jpg)
#   u = x / ancho, v = 1 - y / alto, con x, y en pixeles de la imagen contados desde arriba a la izquierda.
#
# Si una UV cae en varias caras (paredes delgadas con cara de cada lado) salen todas: la buena es la
# que tiene la normal hacia afuera. Si no sale ninguna, esa parte de la imagen no se usa en el modelo.

import bpy, sys, os, mathutils

a = sys.argv[sys.argv.index("--") + 1:]
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(RAIZ, 'modelos', a[0] + '.glb'))
mallas = [o for o in bpy.data.objects if o.type == 'MESH']
T = lambda v: mathutils.Vector((v.x, v.z, -v.y))           # Blender (Z arriba) → three.js (Y arriba)
# la página centra el tenis con la caja de todas sus mallas y lo escala a largo 1
pts = [T(o.matrix_world @ v.co) for o in mallas for v in o.data.vertices]
mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
centro, esc = (mn + mx) / 2, 1 / max(mx - mn)
o = next(o for o in mallas if o.data.materials and o.data.materials[0].name.startswith(a[1]))
me = o.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
for k in range(2, len(a), 2):
    q = mathutils.Vector((float(a[k]), float(a[k + 1])))
    hallado = False
    for t in me.loop_triangles:
        A, B, C = (uv[l].uv for l in t.loops)
        d = (B.y - C.y) * (A.x - C.x) + (C.x - B.x) * (A.y - C.y)
        if abs(d) < 1e-12: continue
        w1 = ((B.y - C.y) * (q.x - C.x) + (C.x - B.x) * (q.y - C.y)) / d
        w2 = ((C.y - A.y) * (q.x - C.x) + (A.x - C.x) * (q.y - C.y)) / d
        w3 = 1 - w1 - w2
        if min(w1, w2, w3) < 0: continue
        P = sum((me.vertices[i].co * w for i, w in zip(t.vertices, (w1, w2, w3))), mathutils.Vector())
        p = (T(o.matrix_world @ P) - centro) * esc
        n = T(o.matrix_world.to_3x3() @ t.normal).normalized()
        print(f'UV {a[k]},{a[k+1]} -> "punto": [{p.x:.4f}, {p.y:.4f}, {p.z:.4f}], "normal": [{n.x:.3f}, {n.y:.3f}, {n.z:.3f}]')
        hallado = True
    if not hallado: print(f'UV {a[k]},{a[k+1]} -> ninguna cara usa esa parte de la textura')
