import bpy
from bpy.types import Context


class Bonedot_PT_ImportSprite(bpy.types.Panel):
    bl_idname = "bonedot.import_sprite_panel"
    bl_label = "Sprite and Mesh"
    bl_options = {"HEADER_LAYOUT_EXPAND"}
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneDot"

    def draw(self, context: Context):
        layout = self.layout
        row = layout.row()
        row.operator("bonedot.import_sprites", text="Import Sprite")
