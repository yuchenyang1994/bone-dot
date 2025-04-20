import bpy
from bpy.types import Context, Event, Object


class Bonedot_OT_ModalUVSyncOperator(bpy.types.Operator):
    bl_idname = "bonedot.modal_uv_sync"
    bl_label = "Start UV Sync"

    def sync_uv_to_vertex(self, obj, scale=0.01):
        w, h = self.get_tex_image_size(obj)
        mesh = obj.data
        uv_layer = mesh.uv_layers.active
        if not uv_layer:
            return

        uv_data = uv_layer.data

        for loop in mesh.loops:
            uv = uv_data[loop.index].uv
            vert = mesh.vertices[loop.vertex_index]
            vert.co.x = (uv.x - 0.5) * w * scale
            vert.co.y = -(uv.y - 0.5) * h * scale

    def get_tex_image_size(self, obj: Object):
        if not obj.data.materials:
            return None

        mat = obj.data.materials[0]
        if not mat.node_tree:
            return None

        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                return node.image.size

    def execute(self, context: Context):
        obj = context.object
        if obj and obj.type == "MESH":
            prev_mode = obj.mode
            bpy.ops.object.mode_set(mode="OBJECT")
            self.sync_uv_to_vertex(obj, context.scene.bonedot_scale)
            bpy.ops.object.mode_set(mode=prev_mode)
            self.report({"INFO"}, "UV synced to mesh vertices")
        else:
            self.report({"WARNING"}, "Select a mesh object")
        return {"FINISHED"}
