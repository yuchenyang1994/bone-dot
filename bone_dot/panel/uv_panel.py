import bpy
from bpy.types import Context


class Bonedot_PT_UVTools(bpy.types.Panel):
    bl_label = "Bonedot UV Tools"
    bl_idname = "BONEDOT_PT_UVTools"
    bl_options = {"HEADER_LAYOUT_EXPAND"}
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "BoneDot"

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()
        row.operator("bonedot.modal_uv_sync", text="UV Sync Vertices")
