import bpy
from bone_dot.panel import viewport_panel, sprite_panel
from bone_dot.operator import view2d_operator, sprite_operator

bl_info = {
    "name": "BoneDot",
    "author": "yuchenyang1994",
    "description": "2d Bone animation tools for Godot",
    "versioin": (0, 1),
    "blender": (4, 4, 0),
    "location": "View3D > Tool Shelf > BoneDot",
    "warning": "",
    "doc_url": "",
    "category": "Development",
}


classes = (
    viewport_panel.Bonedot_PT_ViewPortPanel,
    view2d_operator.Bonedot_OT_View2DSetBottomView,
    # import sprite
    sprite_panel.Bonedot_PT_ImportSprite,
    sprite_operator.Bonedot_OT_ImportSprite,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
