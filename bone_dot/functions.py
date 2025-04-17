import bpy

last_sprite_object = None


def get_sprite_object(obj):
    global last_sprite_object

    if obj is not None:
        if "sprite_object" in obj.coa_tools:
            last_sprite_object = obj.name
            return obj
        elif obj.parent is not None:
            return get_sprite_object(obj.parent)

    if last_sprite_object is not None and last_sprite_object in bpy.data.objects:
        return bpy.data.objects[last_sprite_object]
    return None
