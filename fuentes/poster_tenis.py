# Fotos fijas de un tenis exportado (fondo transparente): respaldo de la página cuando el navegador
# no tiene WebGL y material para redes. Se dibuja como en la página: sin luces, la textura del
# escaneo y la suela con su color horneado.
#
# Uso:
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup ^
#     -P fuentes\poster_tenis.py -- <id> [ancho=1400]
# Escribe modelos/poster/<id>.webp (3/4 del costado exterior, para la página) y
# entregables/renders/<id>.png (2800 px, para redes y presentaciones; fuera de git por su peso).

import bpy, math, mathutils, os, sys

args = sys.argv[sys.argv.index("--") + 1:]
ident = args[0]
ancho = int(args[1]) if len(args) > 1 else 1400
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(RAIZ, 'modelos', 'poster'), exist_ok=True)
os.makedirs(os.path.join(RAIZ, 'entregables', 'renders'), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(RAIZ, 'modelos', ident + '.glb'))
tex = bpy.data.images.load(os.path.join(RAIZ, 'modelos', 'tex', ident + '_4k.jpg'))
mallas = [o for o in bpy.data.objects if o.type == 'MESH']
for o in mallas:
    for m in o.data.materials:
        m.use_nodes = True; nt = m.node_tree
        propia = (bpy.data.images.load(os.path.join(RAIZ, 'modelos', 'tex', ident + '_firmas_4k.jpg'))
                  if m.name.startswith('firmas') else None)
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
        if m.name.startswith('escaneo'):
            src = nt.nodes.new('ShaderNodeTexImage'); src.image = tex; color = src.outputs['Color']
        elif propia:
            # firmas de la suela: su imagen por la luz horneada en los vértices, como en la página
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = propia
            v = nt.nodes.new('ShaderNodeVertexColor'); v.layer_name = o.data.color_attributes[0].name
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs['Factor'].default_value = 1
            nt.links.new(t.outputs['Color'], mx.inputs[6]); nt.links.new(v.outputs['Color'], mx.inputs[7])
            color = mx.outputs[2]
        else:
            src = nt.nodes.new('ShaderNodeVertexColor'); src.layer_name = o.data.color_attributes[0].name
            color = src.outputs['Color']
        nt.links.new(color, em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface'])

pts = [o.matrix_world @ mathutils.Vector(v) for o in mallas for v in o.bound_box]
mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
centro, largo = (mn + mx) / 2, max(mx - mn)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
cam.data.type = 'ORTHO'
sc.collection.objects.link(cam); sc.camera = cam
# la punta queda hacia -Y; el costado exterior es -X en el derecho y +X en el izquierdo
lado = -1 if ident.endswith('_der') else 1
az, el = math.radians(-90 + lado * 62), math.radians(16)
d = largo * 3
cam.location = centro + mathutils.Vector((d*math.cos(el)*math.cos(az), d*math.cos(el)*math.sin(az), d*math.sin(el)))
cam.rotation_euler = (centro - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = largo * 1.32

for sufijo, w, fmt in (('', ancho, 'WEBP'), ('_hd', ancho * 2, 'PNG')):
    sc.render.resolution_x, sc.render.resolution_y = w, int(w * 0.72)
    sc.render.image_settings.file_format = fmt
    sc.render.image_settings.color_mode = 'RGBA'
    if fmt == 'WEBP': sc.render.image_settings.quality = 82
    sc.render.filepath = (os.path.join(RAIZ, 'modelos', 'poster', ident + '.webp') if fmt == 'WEBP'
                          else os.path.join(RAIZ, 'entregables', 'renders', ident + '.png'))
    bpy.ops.render.render(write_still=True)
    print('POSTER', sc.render.filepath, round(os.path.getsize(sc.render.filepath) / 1024), 'KB')
