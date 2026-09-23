# Imagen fija del tenis para cuando el navegador no tiene WebGL (se muestra en lugar del 3D).
# Dibuja el .glb con luz plana, como la página, sobre fondo transparente.
#
# Uso:
#   "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup ^
#     -P fuentes\poster_tenis.py -- modelos\x.glb modelos\x.webp [giro_grados=120]

import bpy, bmesh, math, mathutils, os, sys

args = sys.argv[sys.argv.index("--") + 1:]
entrada, salida = os.path.abspath(args[0]), os.path.abspath(args[1])
giro = math.radians(float(args[2]) if len(args) > 2 else 120)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=entrada)
mallas = [o for o in bpy.data.objects if o.type == 'MESH']

# luz plana: la textura se emite tal cual
for m in bpy.data.materials:
    nt = m.node_tree
    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    emi = nt.nodes.new('ShaderNodeEmission')
    salida_mat = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.links.new(tex.outputs['Color'], emi.inputs['Color'])
    nt.links.new(emi.outputs[0], salida_mat.inputs['Surface'])

pts = [o.matrix_world @ mathutils.Vector(c) for o in mallas for c in o.bound_box]
mn = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
mx = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
centro, largo = (mn + mx) / 2, max(mx - mn)

# mismo recorte que hace la página (TENIS.corteBase en index.html): los últimos milímetros bajo
# la suela todavía traen restos de la base del escaneo
CORTE_BASE = 0.012
for o in mallas:
    bm = bmesh.new(); bm.from_mesh(o.data)
    corte = mn.z + CORTE_BASE * largo
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if (o.matrix_world @ v.co).z < corte], context='VERTS')
    bm.to_mesh(o.data); bm.free()

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 1200, 900
sc.render.image_settings.file_format = 'WEBP'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.quality = 82
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.lens = 70
sc.collection.objects.link(cam); sc.camera = cam
# giro medido como en la página: 0 = talón a la cámara (el tenis es largo en Y de Blender)
d, elev = largo * 2.6, math.radians(14)
cam.location = centro + mathutils.Vector((-math.sin(giro) * math.cos(elev) * d, -math.cos(giro) * math.cos(elev) * d, math.sin(elev) * d))
cam.rotation_euler = (centro - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = salida
bpy.ops.render.render(write_still=True)
print(f"POSTER {salida} ({os.path.getsize(salida) / 1e3:.0f} KB)")
