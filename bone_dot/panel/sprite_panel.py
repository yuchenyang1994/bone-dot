import bpy
from bpy.types import Context


class Bonedot_PT_ImportSprite(bpy.types.Panel):
    bl_label = "Sprite and Mesh"
    bl_idname = "BONEDOT_PT_importsprite_panel"
    bl_options = {"HEADER_LAYOUT_EXPAND"}
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneDot"

    def draw(self, context: Context):
        layout = self.layout
        row1 = layout.row()
        row1.operator(
            "bonedot.import_sprites", text="Import Sprite", icon="FILE_FOLDER"
        )
        row2 = layout.row()
        row2.operator("bonedot.cutoff_mesh", text="Cutoff Mesh", icon="MESH_PLANE")
        row3 = layout.row()
        row3.operator(
            "bonedot.tris_to_quads", text="Tris to Quads", icon="MOD_TRIANGULATE"
        )
