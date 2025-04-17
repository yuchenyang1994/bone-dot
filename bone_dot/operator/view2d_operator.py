import bpy
from bpy.types import Context


class Bonedot_OT_SetView2D(bpy.types.Operator):
    bl_idname = "bonedot.set_2d_view"
    bl_label = "2D View"

    def execute(self, context: Context):
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for region in area.regions:
                    if region.type == "WINDOW":
                        bpy.ops.view3d.view_axis(
                            type="FRONT", align_active=False, relative=False
                        )
                        break
        return {"FINISHED"}
