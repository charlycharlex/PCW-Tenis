# Exporta un tenis ya terminado en Blender (escaneo con firmas + suela reconstruida) para la web.
#
# Uso:
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P fuentes\exportar_tenis.py -- ^
#       fuentes\originales\blend\tenis_azul_derecho.blend azul_der [--girar] [triangulos=100000]
#
# Genera en modelos/:
#   <id>.glb          geometría con Draco. Dos mallas: "escaneo" (con UV, la textura va aparte) y
#                     "suela" (todo lo reconstruido, con su color horneado en los vértices).
#   tex/<id>_1k.jpg, _2k.jpg, _4k.jpg   la textura del escaneo en tres tamaños: la página carga la
#                     que le toca al dispositivo y la de 4K solo al acercarse a una firma.
#
# Por qué hornear la suela: sus materiales son procedurales (ruido + relieve) y la página dibuja sin
# luces (la del escaneo ya viene horneada en su textura). Se hornea su color con una luz de ambiente
# blanca, que es como se ve un escaneo de fotogrametría, y así las dos partes casan.
#
# --girar: los escaneos no vienen todos con la punta hacia el mismo lado. Todos se dejan con la punta
# hacia -Y de Blender (= +Z en three.js); --girar los voltea 180° para lograrlo.

import bpy, bmesh, mathutils, math, os, sys, time

args = sys.argv[sys.argv.index("--") + 1:]
flags = {a for a in args if a.startswith("--")}
args = [a for a in args if not a.startswith("--")]
entrada, ident = os.path.abspath(args[0]), args[1]
tris_escaneo = int(args[2]) if len(args) > 2 else 100000
TRIS_SUELA = 24000
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'modelos')
os.makedirs(os.path.join(SALIDA, 'tex'), exist_ok=True)
t0 = time.time()

bpy.ops.wm.open_mainfile(filepath=entrada)
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

# lo que se ve en el render final (los objetos ocultos son respaldos de quien los editó)
fuentes = [o for o in sc.objects if o.type == 'MESH' and not o.hide_render and o.visible_get()]

def textura_escaneo(mat):
    """La imagen grande conectada al color base: así se reconoce el material del escaneo."""
    if not mat or not mat.node_tree: return None
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            for l in n.inputs['Base Color'].links:
                img = getattr(l.from_node, 'image', None)
                if img and img.size[0] >= 4096: return img
    return None

imagen = None
for o in fuentes:
    for m in o.data.materials:
        imagen = imagen or textura_escaneo(m)
assert imagen, "no encontré la textura del escaneo"

# cada fuente → malla nueva con modificadores aplicados y en coordenadas de mundo
giro = mathutils.Matrix.Rotation(math.pi, 4, 'Z') if '--girar' in flags else mathutils.Matrix.Identity(4)
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
    if o.type == 'LIGHT': o.hide_render = True   # el horneado usa solo la luz de ambiente

# separar por material: escaneo (textura grande) contra todo lo demás (suela, rellenos, parches)
def seleccionar(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]

escaneos, suelas = [], []
for o in piezas:
    es = [i for i, m in enumerate(o.data.materials) if textura_escaneo(m)]
    if not es:
        suelas.append(o); continue
    # hay escaneos con materiales de caucho en la lista que ya ninguna cara usa
    if all(p.material_index in es for p in o.data.polygons):
        escaneos.append(o); continue
    seleccionar([o]); bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(o.data)
    for f in bm.faces: f.select = f.material_index not in es
    bmesh.update_edit_mesh(o.data)
    bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    escaneos.append(o)
    suelas += [x for x in bpy.context.selected_objects if x is not o]

def unir(objs, nombre):
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

escaneo = unir(escaneos, 'escaneo')
suela = unir(suelas, 'suela') if suelas else None
info = {'escaneo_original': contar(escaneo)}
info['escaneo'] = reducir(escaneo, tris_escaneo)
if suela:
    info['suela_original'] = contar(suela)
    # la suela no necesita su resolución original (hasta 650k triángulos para caucho liso)
    for p in suela.data.polygons: p.use_smooth = True
    info['suela'] = reducir(suela, TRIS_SUELA)

# ---- horneado del color de la suela en sus vértices ----
if suela:
    w = bpy.data.worlds.new('ambiente'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 48
    sc.cycles.device = 'CPU'
    attr = suela.data.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    suela.data.color_attributes.active_color = attr
    seleccionar([suela])
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT', 'COLOR'}, target='VERTEX_COLORS')
    # un solo material simple: lo que importa ya está en los vértices
    suela.data.materials.clear()
    ms = bpy.data.materials.new('suela'); ms.use_nodes = True
    nt = ms.node_tree
    vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    nt.links.new(vc.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    suela.data.materials.append(ms)

# el escaneo se exporta sin imagen: la textura viaja aparte para elegir su tamaño en la página
escaneo.data.materials.clear()
me_ = bpy.data.materials.new('escaneo'); escaneo.data.materials.append(me_)
for o in (escaneo, suela):
    if not o: continue
    # basura de la conversión: vértices sueltos
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()

seleccionar([x for x in (escaneo, suela) if x])
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

info['segundos'] = round(time.time() - t0)
print('EXPORTADO', ident, info)
