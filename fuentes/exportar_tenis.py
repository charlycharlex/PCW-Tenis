# Exporta un tenis ya terminado en Blender (escaneo con firmas + suela reconstruida) para la web.
#
# Uso:
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P fuentes\exportar_tenis.py -- ^
#       fuentes\originales\blend\tenis_azul_derecho.blend azul_der [--girar | --giro=-90] [triangulos=100000]
#
# Genera en modelos/:
#   <id>.glb          geometría con Draco. Hasta tres mallas: "escaneo" (con UV, la textura va aparte),
#                     "suela" (todo lo reconstruido, con su color horneado en los vértices) y "firmas"
#                     (ver abajo).
#   tex/<id>_1k.jpg, _2k.jpg, _4k.jpg   la textura del escaneo en tres tamaños: la página carga la
#                     que le toca al dispositivo y la de 4K solo al acercarse a una firma.
#   tex/<id>_firmas_1k|2k|4k.jpg  solo si la suela trae firmas (ver abajo): 1024×256, 2048×512, 4096×1024.
#   tex/<id>_metal.jpg  solo si el escaneo trae máscara de metal (ver abajo).
#
# Por qué hornear la suela: sus materiales son procedurales (ruido + relieve) y la página dibuja sin
# luces (la del escaneo ya viene horneada en su textura). Se hornea su color con una luz de ambiente
# blanca, que es como se ve un escaneo de fotogrametría, y así las dos partes casan. Los materiales
# metálicos se hornean como color plano: con metallic=1 su difuso sale negro.
#
# --girar: los escaneos no vienen todos con la punta hacia el mismo lado. Todos se dejan con la punta
# hacia -Y de Blender (= +Z en three.js); --girar los voltea 180° para lograrlo. --giro=<grados> gira
# lo que haga falta sobre Z (los plateados traen la punta hacia +X: --giro=-90).
#
# Suela con firmas (plateado izquierdo): si una pieza que no es el escaneo trae su propia imagen en el
# color base (firmas reproyectadas sobre el caucho), no se puede hornear a vértices porque el texto se
# perdería. Va como tercera malla, "firmas", con sus UV; su imagen viaja aparte en tres tamaños, como
# la del escaneo (dentro del .glb serían 21 MB de memoria de video aunque el tenis se vea chico). En sus
# vértices se hornea solo la luz de ambiente y la página multiplica las dos cosas.
#
# Cromo (plateados): si el metal del escaneo sale de una imagen ORM (azul = metal), se guarda esa
# máscara en gris a 1K. La página la usa para poner reflejos solo en las piezas metálicas.

import bpy, bmesh, mathutils, math, os, sys, time
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
flags = {a.split('=')[0]: (a.split('=') + [''])[1] for a in args if a.startswith("--")}
args = [a for a in args if not a.startswith("--")]
entrada, ident = os.path.abspath(args[0]), args[1]
tris_escaneo = int(args[2]) if len(args) > 2 else 100000
TRIS_SUELA = 24000
TRIS_FIRMAS = 30000
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'modelos')
os.makedirs(os.path.join(SALIDA, 'tex'), exist_ok=True)
t0 = time.time()

bpy.ops.wm.open_mainfile(filepath=entrada)
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# lo que se ve en el render final (los objetos ocultos son respaldos de quien los editó)
fuentes = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render and o.visible_get()]

def bsdf(mat):
    if not mat or not mat.node_tree: return None
    return next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)

def imagen_color(mat):
    b = bsdf(mat)
    if not b: return None
    for l in b.inputs['Base Color'].links:
        img = getattr(l.from_node, 'image', None)
        if img: return img
    return None

def textura_escaneo(mat):
    """La imagen grande y cuadrada conectada al color base: así se reconoce el material del escaneo
    (el atlas de firmas de la suela también es grande, pero alargado)."""
    img = imagen_color(mat)
    return img if img and img.size[0] >= 4096 and img.size[0] == img.size[1] else None

def tipo(mat):
    if textura_escaneo(mat): return 'escaneo'
    return 'firmas' if imagen_color(mat) else 'suela'

imagen = mat_escaneo = None
for o in fuentes:
    for m in o.data.materials:
        if not imagen and textura_escaneo(m): imagen, mat_escaneo = textura_escaneo(m), m
assert imagen, "no encontré la textura del escaneo"

# máscara de metal: Metallic <- Separate Color (Blue) <- imagen ORM
mascara_metal = None
for l in bsdf(mat_escaneo).inputs['Metallic'].links:
    if l.from_node.type == 'SEPARATE_COLOR' and l.from_socket.name == 'Blue':
        for l2 in l.from_node.inputs[0].links:
            mascara_metal = getattr(l2.from_node, 'image', None)

for m in bpy.data.materials:
    b = bsdf(m)
    if b and not b.inputs['Metallic'].is_linked: b.inputs['Metallic'].default_value = 0.0

# cada fuente → malla nueva con modificadores aplicados y en coordenadas de mundo
grados = 180 if '--girar' in flags else float(flags.get('--giro') or 0)
giro = mathutils.Matrix.Rotation(math.radians(grados), 4, 'Z')
piezas = []
for o in fuentes:
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(giro @ o.matrix_world)
    nuevo = bpy.data.objects.new(o.name + '_web', me)
    sc.collection.objects.link(nuevo)
    piezas.append(nuevo)
for o in fuentes:
    bpy.data.objects.remove(o, do_unlink=True)
for o in list(sc.objects):
    # el horneado usa solo la luz de ambiente, y nada más debe taparla: los plateados traen un plano
    # "Fondo" oculto en la vista pero no en el render, que dejaba negra la cara de abajo de la suela
    if o not in piezas: o.hide_render = True

def seleccionar(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]

# separar por material y clasificar: escaneo, firmas (caucho con imagen) o suela (lo demás)
grupos = {'escaneo': [], 'firmas': [], 'suela': []}
for o in piezas:
    usados = {p.material_index for p in o.data.polygons}
    # hay escaneos con materiales de caucho en la lista que ya ninguna cara usa
    if len({tipo(o.data.materials[i]) for i in usados}) > 1:
        seleccionar([o]); bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
        partes = list(bpy.context.selected_objects)
    else:
        partes = [o]
    for p in partes:
        if not p.data.polygons: continue
        i = p.data.polygons[0].material_index
        grupos[tipo(p.data.materials[i])].append(p)

def unir(objs, nombre):
    # join empata las capas UV por nombre: una pieza con su UV bajo otro nombre (la pared de la suela
    # del plateado usa "Cilindrico_firmas_altura_real", el resto "st") se quedaría con UV en (0,0)
    for o in objs:
        uvs = o.data.uv_layers
        if not len(uvs): continue
        activa = uvs.active.name
        for l in [l.name for l in uvs if l.name != activa]: uvs.remove(uvs[l])
        uvs[activa].name = 'UVMap'
    seleccionar(objs)
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = nombre
    return o

def contar(o):
    o.data.calc_loop_triangles(); return len(o.data.loop_triangles)

def reducir(o, meta):
    n = contar(o)
    if n > meta:
        seleccionar([o])
        mod = o.modifiers.new('dec', 'DECIMATE'); mod.ratio = meta / n
        bpy.ops.object.modifier_apply(modifier='dec')
    return contar(o)

escaneo = unir(grupos['escaneo'], 'escaneo')
suela = unir(grupos['suela'], 'suela') if grupos['suela'] else None
firmas = unir(grupos['firmas'], 'firmas') if grupos['firmas'] else None
info = {'escaneo_original': contar(escaneo)}
info['escaneo'] = reducir(escaneo, tris_escaneo)
for o, meta in ((suela, TRIS_SUELA), (firmas, TRIS_FIRMAS)):
    if not o: continue
    info[o.name + '_original'] = contar(o)
    # la suela no necesita su resolución original (hasta 650k triángulos para caucho liso)
    for p in o.data.polygons: p.use_smooth = True
    info[o.name] = reducir(o, meta)

# ---- horneado en vértices: color + luz en la suela, solo luz en las firmas ----
if suela or firmas:
    w = bpy.data.worlds.new('ambiente'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 48
    sc.cycles.device = 'CPU'
for o, pases in ((suela, {'DIRECT', 'INDIRECT', 'COLOR'}), (firmas, {'DIRECT', 'INDIRECT'})):
    if not o: continue
    attr = o.data.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    o.data.color_attributes.active_color = attr
    seleccionar([o])
    bpy.ops.object.bake(type='DIFFUSE', pass_filter=pases, target='VERTEX_COLORS')

def material_vertices(nombre):
    ms = bpy.data.materials.new(nombre); ms.use_nodes = True
    nt = ms.node_tree
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    nt.links.new(vc.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    return ms

# un solo material simple por malla: lo que importa ya está en los vértices (y en el atlas de firmas,
# que se guarda aparte más abajo)
atlas = None
if suela:
    suela.data.materials.clear(); suela.data.materials.append(material_vertices('suela'))
if firmas:
    atlas = next(imagen_color(m) for m in firmas.data.materials if imagen_color(m))
    firmas.data.materials.clear(); firmas.data.materials.append(material_vertices('firmas'))

# el escaneo se exporta sin imagen: la textura viaja aparte para elegir su tamaño en la página
escaneo.data.materials.clear()
me_ = bpy.data.materials.new('escaneo'); escaneo.data.materials.append(me_)
mallas = [x for x in (escaneo, suela, firmas) if x]
for o in mallas:
    # basura de la conversión: vértices sueltos
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()

seleccionar(mallas)
glb = os.path.join(SALIDA, ident + '.glb')
bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_draco_mesh_compression_enable=True,
                          export_draco_mesh_compression_level=7, export_normals=False,
                          export_texcoords=True, export_vertex_color='ACTIVE', export_materials='EXPORT',
                          export_image_format='NONE', export_apply=True)
info['glb_kb'] = round(os.path.getsize(glb) / 1024)

# texturas del escaneo
for lado, sufijo, calidad in ((4096, '4k', 82), (2048, '2k', 84), (1024, '1k', 85)):
    im = imagen.copy()
    if im.size[0] != lado: im.scale(lado, lado)
    ruta = os.path.join(SALIDA, 'tex', f'{ident}_{sufijo}.jpg')
    im.file_format = 'JPEG'
    im.save(filepath=ruta, quality=calidad)
    info['tex_' + sufijo + '_kb'] = round(os.path.getsize(ruta) / 1024)
    bpy.data.images.remove(im)
    if atlas:
        im = atlas.copy(); im.scale(lado, lado // 4)
        ruta = os.path.join(SALIDA, 'tex', f'{ident}_firmas_{sufijo}.jpg')
        im.file_format = 'JPEG'; im.save(filepath=ruta, quality=calidad + 2)
        info['firmas_' + sufijo + '_kb'] = round(os.path.getsize(ruta) / 1024)
        bpy.data.images.remove(im)

if mascara_metal:
    im = mascara_metal.copy(); im.scale(1024, 1024)
    px = np.empty(1024 * 1024 * 4, np.float32); im.pixels.foreach_get(px)
    azul = px.reshape(-1, 4)[:, 2]
    gris = np.repeat(azul[:, None], 4, 1); gris[:, 3] = 1
    salida = bpy.data.images.new('metal', 1024, 1024, is_data=True)
    salida.pixels.foreach_set(gris.ravel())
    ruta = os.path.join(SALIDA, 'tex', f'{ident}_metal.jpg')
    salida.file_format = 'JPEG'; salida.save(filepath=ruta, quality=80)
    info['metal_kb'] = round(os.path.getsize(ruta) / 1024)

info['segundos'] = round(time.time() - t0)
print('EXPORTADO', ident, info)
