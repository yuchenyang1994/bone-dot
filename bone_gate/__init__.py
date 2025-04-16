import bpy

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


classes = ()


def regiseter():
    print("注册插件", bl_info["name"])
    for cls in classes:
        bpy.utils.register_class(cls)


def unrigister():
    print("注销插件", bl_info["name"])
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
