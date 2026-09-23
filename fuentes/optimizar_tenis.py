# Convierte un escaneo .usdz (fotogrametría) en un .glb ligero para web.
#
# Uso:
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup ^
#     -P fuentes\optimizar_tenis.py -- <entrada.usdz> <salida.glb> [triangulos=80000] [textura=2048] [--renders] [--con-normal]
#
# Con --renders guarda vistas de comparación (original vs. reducido) junto al .glb.
# El normal map se omite por defecto: la página dibuja con luz plana (la luz ya viene horneada
# en la textura) y no lo usa. --con-normal lo conserva.
# Pendiente: compresión KTX2 de texturas y tapar la suela (el escaneo no la tiene).

import bpy, bmesh, mathutils, math, os, sys, colorsys
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
flags = {a for a in args if a.startswith("--")}
args = [a for a in args if not a.startswith("--")]
entrada, salida = os.path.abspath(args[0]), os.path.abspath(args[1])
tris_obj = int(args[2]) if len(args) > 2 else 80000
tex = int(args[3]) if len(args) > 3 else 2048
renders = "--renders" in flags
con_normal = "--con-normal" in flags

# Restos de la base: el escaneo recoge la superficie donde estaba apoyado el tenis como placas
# planas pegadas a la suela. Se reconocen porque miran hacia arriba y están casi al ras del piso;
# la pared de la suela mira de lado y la tapa de abajo mira hacia abajo, así que no se tocan.
# Otros quedan como cortinas casi verticales: esos se reconocen por color, gris claro contra
# una suela de color. Ojo con tenis de suela blanca: ahí hay que desactivar BASE_SATURACION (= 0).
BASE_ALTO = 0.012        # m sobre el punto más bajo
BASE_NORMAL_Z = 0.6      # qué tan "hacia arriba" tiene que mirar la cara
BASE_ALTO_COLOR = 0.03   # hasta dónde se busca por color
BASE_SATURACION = 0.22   # debajo de esto es gris/blanco...
BASE_VALOR = 0.5         # ...y encima de esto es claro (la tinta negra de las firmas no se toca)
ISLA_MIN = 200           # caras: una isla más chica que esto es basura suelta

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.usd_import(filepath=entrada)
o = [o for o in bpy.data.objects if o.type == 'MESH'][0]

def contar():
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)

tris_orig = contar()
print(f"ORIGINAL {tris_orig} triangulos, texturas {[tuple(i.size) for i in bpy.data.images]}")

# Vistas de comparación: cámara orbitando a la altura del tenis.
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 900, 700
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.9, 0.9, 1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam); sc.camera = cam

def vista(nombre, az, el, dist=0.75):
    a, e = math.radians(az), math.radians(el)
    cam.location = (dist * math.cos(e) * math.cos(a), dist * math.cos(e) * math.sin(a), dist * math.sin(e))
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.splitext(salida)[0] + f"_{nombre}.png"
    bpy.ops.render.render(write_still=True)

vistas = [("lado_a", 0, 15), ("lado_b", 180, 15), ("punta", 90, 8), ("talon", -90, 8)]
if renders:
    for n, az, el in vistas: vista("orig_" + n, az, el)

# Reducir polígonos conservando las UV (collapse) y bajar texturas.
bpy.context.view_layer.objects.active = o
if tris_orig > tris_obj:
    mod = o.modifiers.new("dec", 'DECIMATE'); mod.ratio = tris_obj / tris_orig
    bpy.ops.object.modifier_apply(modifier="dec")
for im in bpy.data.images:
    if im.size[0] > tex: im.scale(tex, tex)

# Limpiar restos de la base (en coordenadas de mundo: el importador de USD puede rotar el objeto).
# Se hace ya reducido: son 10 veces menos caras y la textura de 2K cabe en memoria para muestrearla.
mw = o.matrix_world
rot = mw.to_3x3()
difusa = next(i for i in bpy.data.images if 'diffuse' in i.name.lower())
W, H = difusa.size
pix = np.empty(W * H * 4, np.float32); difusa.pixels.foreach_get(pix)
pix = pix.reshape(H, W, 4)

def color(f, uv):
    u = sum(l[uv].uv.x for l in f.loops) / len(f.loops)
    v = sum(l[uv].uv.y for l in f.loops) / len(f.loops)
    r, g, b, _ = pix[min(H - 1, int(v % 1 * H)), min(W - 1, int(u % 1 * W))]
    return colorsys.rgb_to_hsv(r, g, b)

bm = bmesh.new(); bm.from_mesh(o.data)
uv = bm.loops.layers.uv.active
piso = min((mw @ v.co).z for v in bm.verts)
por_normal = por_color = 0
restos = []
for f in bm.faces:
    alto = (mw @ f.calc_center_median()).z - piso
    if alto > BASE_ALTO_COLOR: continue
    if alto < BASE_ALTO and (rot @ f.normal).normalized().z > BASE_NORMAL_Z:
        restos.append(f); por_normal += 1
        continue
    _, s, val = color(f, uv)
    if s < BASE_SATURACION and val > BASE_VALOR:
        restos.append(f); por_color += 1
bmesh.ops.delete(bm, geom=restos, context='FACES')

# Lo que quedó suelto (pedacitos de base ya sin conexión con el tenis). La conectividad se mide
# por posición: en las costuras de UV los vértices vienen duplicados y, contando solo aristas,
# cada parche de textura parecería una isla aparte.
padre = {}
def raiz(k):
    while padre[k] != k: padre[k] = padre[padre[k]]; k = padre[k]
    return k
def clave(v): return (round(v.co.x * 1e5), round(v.co.y * 1e5), round(v.co.z * 1e5))
for v in bm.verts: padre.setdefault(clave(v), clave(v))
for f in bm.faces:
    ks = [raiz(clave(v)) for v in f.verts]
    for k in ks[1:]: padre[raiz(k)] = raiz(ks[0])
islas = {}
for f in bm.faces: islas.setdefault(raiz(clave(f.verts[0])), []).append(f)
sueltas = [f for isla in islas.values() if len(isla) < ISLA_MIN for f in isla]
bmesh.ops.delete(bm, geom=sueltas, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(o.data); bm.free()
print(f"LIMPIEZA {por_normal} caras por mirar arriba, {por_color} por color, {len(sueltas)} en islas sueltas")
if not con_normal:
    for m in o.data.materials:
        for n in [n for n in m.node_tree.nodes if n.type == 'NORMAL_MAP']:
            for enlace in list(n.outputs[0].links): m.node_tree.links.remove(enlace)
print(f"REDUCIDO {contar()} triangulos, texturas {tex}px, normal map {'sí' if con_normal else 'no'}")

if renders:
    for n, az, el in vistas: vista("web_" + n, az, el)

bpy.ops.export_scene.gltf(filepath=salida, export_draco_mesh_compression_enable=True,
                          export_image_format='JPEG', export_jpeg_quality=85)
print(f"EXPORTADO {salida} ({os.path.getsize(salida) / 1e6:.2f} MB)")
