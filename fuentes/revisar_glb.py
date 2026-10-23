# Hoja de revisión de un tenis exportado, dibujado como en la página: sin luces, el escaneo con su
# textura y la suela con su color horneado en los vértices. 4 vistas en 2x2.
#
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup -P fuentes\revisar_glb.py -- <id> <salida.jpg>

import bpy, sys, os, math, mathutils
import numpy as np

ident, salida = sys.argv[sys.argv.index("--") + 1:][:2]
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(RAIZ, 'modelos', ident + '.glb'))
tex = bpy.data.images.load(os.path.join(RAIZ, 'modelos', 'tex', ident + '_2k.jpg'))

def plano(mat, color_desde):
    mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(color_desde(nt), em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface'])

mallas = [o for o in bpy.data.objects if o.type == 'MESH']
for o in mallas:
    for m in o.data.materials:
        propia = (bpy.data.images.load(os.path.join(RAIZ, 'modelos', 'tex', ident + '_firmas_2k.jpg'))
                  if m.name.startswith('firmas') else None)
        if m.name.startswith('escaneo'):
            def c(nt):
                n = nt.nodes.new('ShaderNodeTexImage'); n.image = tex; return n.outputs['Color']
        elif propia:
            # firmas de la suela: su imagen por la luz horneada en los vértices, como en la página
            def c(nt, img=propia, capa=o.data.color_attributes[0].name):
                t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
                v = nt.nodes.new('ShaderNodeVertexColor'); v.layer_name = capa
                mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                mx.inputs['Factor'].default_value = 1
                nt.links.new(t.outputs['Color'], mx.inputs[6]); nt.links.new(v.outputs['Color'], mx.inputs[7])
                return mx.outputs[2]
        else:
            def c(nt):
                n = nt.nodes.new('ShaderNodeVertexColor'); n.layer_name = o.data.color_attributes[0].name if o.data.color_attributes else 'Color'; return n.outputs['Color']
        plano(m, c)

pts = [o.matrix_world @ mathutils.Vector(v) for o in mallas for v in o.bound_box]
mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)]); mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
c0, largo = (mn + mx) / 2, max(mx - mn)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 800, 560
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.42, 0.42, 0.44, 1)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); cam.data.lens = 60
sc.collection.objects.link(cam); sc.camera = cam
# el importador deja Z arriba; la punta queda hacia -Y
vistas = [(0, 12), (180, 12), (-90, 10), (200, 55)]
imgs = []
for az, el in vistas:
    a, e = math.radians(az), math.radians(el); d = largo * 2.4
    cam.location = c0 + mathutils.Vector((d*math.cos(e)*math.cos(a), d*math.cos(e)*math.sin(a), d*math.sin(e)))
    cam.rotation_euler = (c0 - cam.location).to_track_quat('-Z', 'Y').to_euler()
    p = salida + '_tmp.png'; sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p)
    imgs.append(np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4))
    bpy.data.images.remove(im); os.remove(p)
hoja = np.concatenate([np.concatenate(imgs[2:], 1), np.concatenate(imgs[:2], 1)], 0)
res = bpy.data.images.new('hoja', hoja.shape[1], hoja.shape[0]); res.pixels = hoja.ravel()
res.file_format = 'JPEG'; res.save(filepath=salida, quality=85)
print('REVISION', salida)
