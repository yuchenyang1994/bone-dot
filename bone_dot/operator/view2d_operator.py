import bpy
from bpy.types import Context


class View2DSetFrontView(bpy.types.Operator):
    bl_idname = "view3d.set_2d_view"
    bl_label = "2D View"

    def execute(self, context: Context):
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "WINDOW":
                        bpy.ops.view3d.view_axis(type="BOTTOM")
                        break
        return {"FINISHED"}
