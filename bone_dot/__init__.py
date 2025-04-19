import bpy
import sys
import os
import subprocess

from bpy.props import BoolProperty

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


def install_wheels():
    addon_dir = os.path.dirname(__file__)
    libs_dir = os.path.join(addon_dir, "lib")
    wheels = [
        os.path.join(libs_dir, f) for f in os.listdir(libs_dir) if f.endswith(".whl")
    ]
    subprocess.check_call([sys.executable, "-m", "ensurepip"])
    for wheel_path in wheels:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", wheel_path]
        )


def get_classes():
    from bone_dot.panel import viewport_panel, sprite_panel
    from bone_dot.operator import (
        view2d_operator,
        sprite_operator,
        mesh_operator,
        uv_operator,
    )

    classes = (
        viewport_panel.Bonedot_PT_ViewPortPanel,
        view2d_operator.Bonedot_OT_SetView2D,
        # import sprite
        sprite_panel.Bonedot_PT_ImportSprite,
        sprite_operator.Bonedot_OT_ImportSprites,
        sprite_operator.Bonedot_OT_CreateMaterialGroup,
        sprite_operator.Bonedot_OT_ImportSingleSprite,
        mesh_operator.Bonedot_OT_CutoffMesh,
        mesh_operator.Bonedot_OT_TrisToQuads,
        uv_operator.Bonedot_OT_ModalUVSyncOperator,
    )
    return classes


def register():
    try:
        import PIL
        import numpy
    except ImportError:
        install_wheels()
    bpy.types.Scene.realtime_uv_sync = BoolProperty(
        name="Realtime UV Sync",
        description="Enable realtime UV to Vertex sync",
        default=False,
    )
    classes = get_classes()
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    classes = get_classes()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.realtime_uv_sync


if __name__ == "__main__":
    try:
        unregister()
    except Exception as e:
        print("unregister failed!", e)
    register()
