import bpy
import os
from bpy.types import Context
from PIL import Image


class Bonedot_OT_CutoffMesh(bpy.types.Operator):
    bl_idname = "bonedot.cutoff_mesh"
    bl_label = "Cutoff Mesh"
    bl_description = "Cutoff mesh form image"
    bl_options = {"REGISTER", "UNDO"}

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
            edge_points = self.extract_alpha_edge_points(pil_img)
            print(edge_points)

            return {"FINISHED"}

    def extract_alpha_edge_points(self, pil_image: Image.Image, sample_step=4):
        w, h = pil_image.size
        alpha = pil_image.getchannel("A")
        alpha_data = alpha.load()

        edge_points = []

        for y in range(1, h - 1, sample_step):
            for x in range(1, w - 1, sample_step):
                a = alpha_data[x, y]
                if a > 0:
                    neighbors = [
                        alpha_data[x + 1, y],
                        alpha_data[x - 1, y],
                        alpha_data[x, y + 1],
                        alpha_data[x, y - 1],
                    ]
                    if any(n == 0 for n in neighbors):
                        edge_points.append((x, y))
        return edge_points
