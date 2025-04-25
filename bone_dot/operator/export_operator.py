from typing import List
import os
import bpy
from bpy.types import Armature, Context, Image, Object
from mathutils import Vector
from math import atan2
from math import isclose


class Bonedot_OT_ExportAnimation(bpy.types.Operator):
    bl_idname = "bonedot.export_animation"
    bl_label = "Export Animation"
    bl_description = "Export Animation"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="保存为.bdsket文件",
        subtype="FILE_PATH",
        options={"SKIP_SAVE"},
        filter_glob="*.bdsket",
    )

    def execute(self, context: Context):
        if not context.selected_objects:
            self.report({"ERROR", "Please select Armature"})
            return {"CANCELLED"}
        armatures = []
        for obj in context.selected_objects:
            if obj.type != "ARMATURE":
                self.report({"ERROR", "Please select Armature"})
                continue
            meshes = [child for child in obj.children if child.type == "MESH"]
            images = self.find_mesh_texture_images(context, meshes)
            textures = [
                {
                    "texture": f"textures/{os.path.basename(image.filepath)}",
                    "size": image.size,
                }
                for image in images
            ]
            meshes = [self.extract_mesh_data(mesh) for mesh in meshes]
            bones = self.extract_skeleton_data(obj)
            animation = self.extract_animation(obj)
            armatures.append(
                {
                    "textures": textures,
                    "meshes": meshes,
                    "bones": bones,
                    "animations": animation,
                }
            )
        print(armatures)
        return {"FINISHED"}

    def find_mesh_texture_images(
        self, context: Context, meshes: List[Object]
    ) -> List[Image]:
        images = []
        for mesh in meshes:
            for mat_slot in mesh.material_slots:
                if mat_slot.material and mat_slot.material.node_tree:
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == "TEX_IMAGE" and node.image:
                            images.append(node.image)
        return images

    def extract_mesh_data(self, mesh_obj: Object):
        mesh = mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
        world_matrix = mesh_obj.matrix_world
        vertices = [
            [round((world_matrix @ v.co).x, 6), round((world_matrix @ v.co).y, 6)]
            for v in mesh.vertices
        ]
        uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        uvs = [[0.0, 0.0] for _ in range(len(mesh.vertices))]
        if uv_layer:
            for loop in mesh.loops:
                uv = uv_layer[loop.index].uv
                vert_index = loop.vertex_index
                uvs[vert_index] = [round(uv.x, 6), round(uv.y, 6)]
        triangles = []
        for poly in mesh.polygons:
            if len(poly.vertices) == 3:
                triangles.append(list(poly.vertices))
            elif len(poly.vertices) > 3:
                for i in range(1, len(poly.vertices) - 1):
                    triangles.append(
                        [poly.vertices[0], poly.vertices[i], poly.vertices[i + 1]]
                    )

        origin_world = world_matrix @ Vector((0, 0, 0))
        z_hint = round(origin_world.z, 6)
        return {
            "name": mesh_obj.name.split(".")[0],
            "vertices": vertices,
            "uvs": uvs,
            "triangles": triangles,
            "texture": mesh_obj.name,
            "z_hint": z_hint,
            "weights": self.extract_weights_dict_per_mesh(mesh_obj),
        }

    def extract_skeleton_data(self, obj: Object):
        armature_data = obj.data
        bones = []

        for bone in armature_data.bones:
            head = obj.matrix_world @ bone.head_local
            tail = obj.matrix_world @ bone.tail_local
            angle = atan2(tail.y - head.y, tail.x - head.x)

            bones.append(
                {
                    "name": bone.name,
                    "parent": bone.parent.name if bone.parent else None,
                    "head": [round(head.x, 6), round(head.y, 6)],
                    "tail": [round(tail.x, 6), round(tail.y, 6)],
                    "angle": round(angle, 6),
                }
            )

    def extract_weights_dict_per_mesh(mesh_obj: Object):
        mesh_data = mesh_obj.data
        vertex_groups = mesh_obj.vertex_groups

        vg_map = {vg.index: vg.name for vg in vertex_groups}

        weights = [{} for _ in mesh_data.vertices]

        for v in mesh_data.vertices:
            for g in v.groups:
                bone_name = vg_map.get(g.group)
                if bone_name:
                    weights[v.index][bone_name] = round(g.weight, 6)

        return weights

    def extract_animation(self, obj: Object):
        animations = []
        for action in bpy.data.actions:
            if self._action_affects_armature(action, obj):
                frame_start, frame_end = action.frame_range
                anima_data = self.bake_animation(obj, action, frame_start, frame_end)
                animations.append({"name": action.name, "data": anima_data})
        return animations

    def bake_animation(
        self, armature_obj, action, frame_start, frame_end, epsilon=1e-5
    ):
        bpy.context.view_layer.objects.active = armature_obj
        duplicated_action = action.copy()
        duplicated_action.name = action.name + "_baked"

        armature_obj.animation_data.action = duplicated_action
        bpy.ops.nla.bake(
            frame_start=int(frame_start),
            frame_end=int(frame_end),
            only_selected=False,
            visual_keying=True,
            clear_constraints=False,
            use_current_action=True,
            bake_types={"POSE"},
        )
        pose_bones = armature_obj.pose.bones
        bone_tracks = {}

        for bone in pose_bones:
            loc_track = []
            rot_track = []

            prev_loc = None
            prev_rot = None

            for frame in range(int(frame_start), int(frame_end) + 1):
                bpy.context.scene.frame_set(frame)

                mat = bone.matrix
                pos = mat.to_translation()
                angle = mat.to_euler("XYZ").z

                loc2d = [round(pos.x, 6), round(pos.y, 6)]
                ang = round(angle, 6)

                if (
                    prev_loc is None
                    or not isclose(prev_loc[0], loc2d[0], abs_tol=epsilon)
                    or not isclose(prev_loc[1], loc2d[1], abs_tol=epsilon)
                ):
                    loc_track.append([frame, loc2d[0], loc2d[1]])
                    prev_loc = loc2d

                if prev_rot is None or not isclose(prev_rot, ang, abs_tol=epsilon):
                    rot_track.append([frame, ang])
                    prev_rot = ang

            bone_tracks[bone.name] = {
                "bone": bone.name,
                "location": loc_track,
                "rotation": rot_track,
            }
        return {
            "fps": int(frame_end - frame_start + 1),
            "tracks": list(bone_tracks.values()),
        }

    def _action_affects_armature(self, action, armature_obj):

        for fcurve in action.fcurves:
            # e.g., 'pose.bones["upper_arm"].rotation_euler'
            if fcurve.data_path.startswith("pose.bones["):
                bone_name = fcurve.data_path.split('"')[1]
                if bone_name in armature_obj.pose.bones:
                    return True
        return False
