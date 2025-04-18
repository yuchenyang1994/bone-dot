import bmesh
import bpy
import os
from bpy.types import Context, Event
from PIL import Image
import numpy as np
from mathutils import Matrix, Vector


class Bonedot_OT_CutoffMesh(bpy.types.Operator):
    bl_idname = "bonedot.cutoff_mesh"
    bl_label = "Cutoff Mesh"
    bl_description = "Cutoff mesh form image"
    bl_options = {"REGISTER", "UNDO"}

    cut_sample_rate: bpy.props.IntProperty(name="Cut Sample Rate", default=16)

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context):
        layout = self.layout
        layout.prop(self, "cut_sample_rate")

    def execute(self, context: Context):
        for obj in context.selected_objects:
            if obj is None:
                self.report({"ERROR"}, "no selected object")
                return {"CANCELLED"}

            if obj.type != "MESH":
                self.report({"ERROR"}, "object is not mesh")
                return {"CANCELLED"}

            if not (
                obj.data is not None
                and len(obj.data.polygons) == 1
                and len(obj.data.vertices) == 4
            ):
                self.report({"ERROR"}, "object is not plane")
                return {"CANCELLED"}

            mat = obj.active_material
            if not mat or not mat.use_nodes:
                self.report({"ERROR"}, "object not have materials node")
                return {"CANCELLED"}

            img: bpy.types.Image = None
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    img = node.image
                    break
            else:
                self.report({"ERROR"}, "can't find image node")
                return {"CANCELLED"}

            if img.packed_file:
                self.report({"ERROR"}, "image is packed file can't load")
                return {"CANCELLED"}

            filepath = bpy.path.abspath(img.filepath)

            if not os.path.exists(filepath):
                self.report({"ERROR"}, "can't find image path")
                return {"CANCELLED"}

            pil_img = Image.open(filepath).convert("RGBA")
            edge_points = self.trace_alpha_contour(pil_img)
            contour_px = edge_points[:: self.cut_sample_rate]
            cutter_obj = self.make_cutter_mesh(
                "cut_tool", contour_px, pil_img.size, 0.01
            )
            self.boolean_difference(context, obj, cutter_obj)
            return {"FINISHED"}

    def trace_alpha_contour(self, pil_image: Image.Image, alpha_thresh=1):
        w, h = pil_image.size
        alpha = pil_image.getchannel("A")
        alpha_data = alpha.load()

        # 二值化
        mask = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                mask[y, x] = alpha_data[x, y] >= alpha_thresh

        dirs = [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]
        start = None
        for y in range(h):
            for x in range(w):
                if not mask[y, x]:
                    continue
                for dx, dy in dirs:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or not mask[ny, nx]:
                        start = (x, y)
                        break
                if start:
                    break
            if start:
                break
        if not start:
            return []

        contour = [start]
        curr = start
        prev_dir = 7

        while True:
            found = False
            for i in range(1, 9):
                d = (prev_dir + i) % 8
                dx, dy = dirs[d]
                nx, ny = curr[0] + dx, curr[1] + dy
                if 0 <= nx < w and 0 <= ny < h and mask[ny, nx]:
                    contour.append((nx, ny))
                    prev_dir = (d + 4) % 8
                    curr = (nx, ny)
                    found = True
                    break
            if not found or curr == start:
                break

        return contour

    def make_cutter_mesh(self, name, contour_px, image_size, scale):
        w, h = image_size
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)

        bm = bmesh.new()
        verts = [bm.verts.new(self.pixel_to_local(p, w, h, scale)) for p in contour_px]
        bm.verts.ensure_lookup_table()
        try:
            bm.faces.new(verts)
        except ValueError:
            pass
        bm.to_mesh(mesh)
        bm.free()

        return obj

    def boolean_difference(self, context, obj, cutter):
        # 让位置相同
        target_matrix = obj.matrix_world.copy()
        cutter.matrix_world = Matrix.Identity(4)
        cutter.location = target_matrix.to_translation()
        # 把刀具稍微抬高一点，避免 Z-fighting,但我们都是fontview，所以我们需要将y设置为-的
        cutter.location.z -= 0.01

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        cutter.select_set(True)
        bpy.ops.mesh.knife_project(cut_through=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.data.objects.remove(cutter, do_unlink=True)

    def pixel_to_local(self, p, w, h, scale):
        x, y = p
        u = x / w
        v = 1 - (y / h)
        lx = (u - 0.5) * w * scale
        lz = (v - 0.5) * h * scale
        return Vector((lx, 0, lz))


class Bonedot_OT_TrisToQuads(bpy.types.Operator):
    bl_idname = "bonedot.tris_to_quads"
    bl_label = "Tris to Quads"
    bl_description = "Tris to Quads"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        for obj in context.selected_objects:
            if obj.type == "MESH":
                mesh = obj.data
                bm = bmesh.new()
                bm.from_mesh(mesh)

                bmesh.ops.triangulate(bm, faces=bm.faces[:])
                bm.to_mesh(mesh)
                bm.free()

        return {"FINISHED"}
