import bpy

import os
import sys

addon_dir = os.path.dirname(__file__)
vendor_dir = os.path.join(addon_dir, "libs")

if vendor_dir not in sys.path:
    sys.path.append(vendor_dir)
    print(vendor_dir)

from bone_dot.panel import viewport_panel, sprite_panel
from bone_dot.operator import view2d_operator, sprite_operator, mesh_poerator


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
    view2d_operator.Bonedot_OT_SetView2D,
    # import sprite
    sprite_panel.Bonedot_PT_ImportSprite,
    sprite_operator.Bonedot_OT_ImportSprites,
    sprite_operator.Bonedot_OT_CreateMaterialGroup,
    sprite_operator.Bonedot_OT_ImportSingleSprite,
    mesh_poerator.Bonedot_OT_CutoffMesh,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
