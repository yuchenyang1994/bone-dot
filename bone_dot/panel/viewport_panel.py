import bpy
from bpy.types import Context


class ViewPortPanel(bpy.types.Panel):
    bl_label = "Viewport Settings"
    bl_idname = "viewport_settings_operator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneDot"

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()
        row.operator("view3d.set_2d_view", text="2D View")
