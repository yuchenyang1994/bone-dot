import bpy
import bmesh
from bpy.types import Context
from bone_dot import functions
from bpy.props import (
    CollectionProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    BoolProperty,
)
import os
from mathutils import Vector

from bpy_extras.io_utils import ImportHelper


class Bonedot_OT_CreateMaterialGroup(bpy.types.Operator):
    bl_idname = "bonedot.create_material_group"
    bl_label = "Create COA Tools Node Group"
    bl_description = "Creates the default COA Tools Node Group"
    bl_options = {"REGISTER"}

    input_sockets = [
        {"type": "NodeSocketColor", "label": "Texture Color"},
        {
            "type": "NodeSocketFloat",
            "label": "Texture Alpha",
            "min_value": 0.0,
            "max_value": 1.0,
        },
        {"type": "NodeSocketColor", "label": "Modulate Color"},
        {
            "type": "NodeSocketFloat",
            "label": "Alpha",
            "min_value": 0.0,
            "max_value": 1.0,
        },
    ]
    output_sockets = [
        {"type": "NodeSocketShader", "label": "BSDF"},
    ]

    @classmethod
    def poll(cls, context: Context):
        return True

    def create_sockets(self, group_tree):
        inputs = []
        for input_socket in self.input_sockets:
            inputs.append(input_socket["label"])
            if input_socket["label"] not in group_tree.interface.items_tree:
                socket = group_tree.interface.new_socket(
                    input_socket["label"],
                    description="",
                    in_out="INPUT",
                    socket_type=input_socket["type"],
                )

                if "min_value" in input_socket:
                    socket.min_value = input_socket["min_value"]
                if "max_value" in input_socket:
                    socket.max_value = input_socket["max_value"]

        outputs = []
        for output_socket in self.output_sockets:
            outputs.append(output_socket["label"])
            if output_socket["label"] not in group_tree.interface.items_tree:
                socket = group_tree.interface.new_socket(
                    output_socket["label"],
                    description="",
                    in_out="OUTPUT",
                    socket_type=output_socket["type"],
                )
                if "min_value" in output_socket:
                    socket.min_value = output_socket["min_value"]
                if "max_value" in output_socket:
                    socket.max = output_socket["max_value"]

        for socket in group_tree.interface.items_tree:
            if socket.name not in inputs and socket.in_out == "INPUT":
                group_tree.interface.remove(socket)
            elif socket.name not in outputs and socket.in_out == "OUTPUT":
                group_tree.interface.remove(socket)

    def create_coa_material_group(self):
        group_tree = None

        # cleanup group if already existent
        if "Bonedot Material" in bpy.data.node_groups:
            group_tree = bpy.data.node_groups["Bonedot Material"]
            for node in group_tree.nodes:
                group_tree.nodes.remove(node)
        else:
            group_tree = bpy.data.node_groups.new("Bonedot Material", "ShaderNodeTree")
        # recreate group from scratch to ensure to be always latest version

        # create input/output sockets
        self.create_sockets(group_tree)

        # create nodes
        input_node = group_tree.nodes.new("NodeGroupInput")
        output_node = group_tree.nodes.new("NodeGroupOutput")
        principled_node = group_tree.nodes.new("ShaderNodeBsdfPrincipled")
        modulate_node = group_tree.nodes.new("ShaderNodeMixRGB")
        modulate_node.blend_type = "MULTIPLY"
        modulate_node.inputs[0].default_value = 1.0
        modulate_node.inputs[1].default_value = [1, 1, 1, 1]
        modulate_node.inputs[2].default_value = [1, 1, 1, 1]
        alpha_node = group_tree.nodes.new("ShaderNodeMath")
        alpha_node.operation = "MULTIPLY"
        alpha_node.inputs[0].default_value = 1.0
        alpha_node.inputs[1].default_value = 1.0

        # link node sockets
        group_tree.links.new(
            input_node.outputs["Texture Color"], modulate_node.inputs["Color1"]
        )
        group_tree.links.new(
            input_node.outputs["Modulate Color"], modulate_node.inputs["Color2"]
        )
        group_tree.links.new(input_node.outputs["Texture Alpha"], alpha_node.inputs[0])
        group_tree.links.new(input_node.outputs["Alpha"], alpha_node.inputs[1])

        group_tree.links.new(
            modulate_node.outputs["Color"], principled_node.inputs["Base Color"]
        )
        group_tree.links.new(
            modulate_node.outputs["Color"], principled_node.inputs["Emission Color"]
        )

        group_tree.links.new(alpha_node.outputs[0], principled_node.inputs["Alpha"])
        group_tree.links.new(
            principled_node.outputs["BSDF"], output_node.inputs["BSDF"]
        )

        # setup principled node
        principled_node.inputs["Specular IOR Level"].default_value = 0
        principled_node.inputs["Roughness"].default_value = 0
        principled_node.inputs["Coat Roughness"].default_value = 0
        principled_node.inputs["Emission Strength"].default_value = 1

        # position nodes
        input_node.location = [0, 0]
        modulate_node.location = [180, 0]
        alpha_node.location = [180, -200]
        principled_node.location = [360, 0]
        output_node.location = [640, 0]

        return group_tree

    def execute(self, context: Context):
        self.create_coa_material_group()
        return {"FINISHED"}


# Import Single Sprite


class Bonedot_OT_ImportSingleSprite(bpy.types.Operator):
    bl_idname = "bonedot.import_sprite"
    bl_label = "Import Sprite"
    bl_options = {"REGISTER", "UNDO"}

    path: StringProperty(name="Sprite Path", default="", subtype="FILE_PATH")
    pos: FloatVectorProperty(default=Vector((0, 0, 0)))
    scale: FloatProperty(name="Sprite Scale", default=0.01)
    offset: FloatVectorProperty(default=Vector((0, 0, 0)))
    tilesize: FloatVectorProperty(default=Vector((1, 1)), size=2)
    parent: StringProperty(name="Parent Object", default="None")

    def execute(self, context: Context):
        if os.path.exists(self.path):
            data = bpy.data
            sprite_name = os.path.basename(self.path)
            sprite_found = False

            # find image
            for image in bpy.data.images:
                if os.path.exists(bpy.path.abspath(image.filepath)) and os.path.exists(
                    self.path
                ):
                    if os.path.samefile(bpy.path.abspath(image.filepath), self.path):
                        sprite_found = True
                        img = image
                        img.reload()
                        break
            if not sprite_found:
                img = data.images.load(self.path)
            obj = self.create_mesh(
                context,
                name=image.name,
                width=img.size[0],
                height=img.size[1],
                pos=self.pos,
            )
            mat = self.create_material(context, obj.data, name=img.name)

            selected_objects = []
            for obj2 in context.selected_objects:
                selected_objects.append(obj2)
                if obj2 != context.active_object:
                    obj.select_set(False)
            for obj2 in selected_objects:
                obj.select_set(True)
            self.report({"INFO"}, f"{img.name} is imported")
            return {"FINISHED"}
        else:
            self.report({"WARRING"}, "File does not exists.")
            return {"CANCELLED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def create_verts(self, width, height, pos, me, tag_hide=False):
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(me)
        vert1 = bm.verts.new(Vector((0, 0, -height)) * self.scale)
        vert2 = bm.verts.new(Vector((width, 0, -height)) * self.scale)
        vert3 = bm.verts.new(Vector((width, 0, 0)) * self.scale)
        vert4 = bm.verts.new(Vector((0, 0, 0)) * self.scale)

        bm.faces.new([vert1, vert2, vert3, vert4])

        bmesh.update_edit_mesh(me)

        if tag_hide:
            for vert in bm.verts:
                vert.hide_viewport = True

            for edge in bm.edges:
                edge.hide_viewport = True

        bmesh.update_edit_mesh(me)
        bpy.ops.object.mode_set(mode="OBJECT")

    def create_mesh(
        self,
        context: Context,
        name="Sprite",
        width=100,
        height=100,
        pos=Vector((0, 0, 0)),
    ):
        me = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, me)
        context.scene.view_layers[0].objects.active = obj
        obj.select_set(True)

        self.create_verts(width, height, pos, me, tag_hide=False)
        v_group = obj.vertex_groups.new(name="bonedot_base_sprite")
        v_group.add([0, 1, 2, 3], 1.0, "REPLACE")
        v_group.lock_weight = True
        mod = obj.modifiers.new("bonedot_base_sprite", "MASK")
        mod.vertex_group = "bonedot_base_sprite"
        mod.invert_vertex_group = True
        mod.show_in_editmode = True
        mod.show_render = False
        mod.show_viewport = False
        mod.show_on_cage = True
        obj.data.uv_layers.new(name="UVMap")
        obj.location = (
            Vector((pos[0], pos[1], -pos[2])) * self.scale
            + Vector((self.offset[0], self.offset[1], self.offset[2])) * self.scale
        )
        obj.bonedot["sprite"] = True
        if self.parent != "None":
            obj.parent = bpy.data.objects[self.parent]
        return obj

    def create_material(self, context, mesh, name="Sprite"):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        mat.blend_method = "BLEND"
        node_tree = mat.node_tree
        output_node = None

        for node in mat.node_tree.nodes:
            if node.type != "OUTPUT_MATERIAL":
                mat.node_tree.nodes.remove(node)
            else:
                output_node = node

        tex_node = node_tree.nodes.new("ShaderNodeTexImage")
        tex_node.interpolation = "Closest"
        tex_node.image = bpy.data.images[name]
        bpy.ops.bonedot.create_material_group()
        bonedot_node_tree = bpy.data.node_groups["Bonedot Material"]
        bonedot_node = node_tree.nodes.new("ShaderNodeGroup")
        bonedot_node.name = "Bonedot Material"
        bonedot_node.label = "Bonedot Material"
        bonedot_node.node_tree = bonedot_node_tree
        bonedot_node.inputs["Alpha"].default_value = 1.0
        bonedot_node.inputs["Modulate Color"].default_value = [1, 1, 1, 1]

        node_tree.links.new(
            bonedot_node.inputs["Texture Color"],
            tex_node.outputs["Color"],
            verify_limits=True,
        )
        node_tree.links.new(
            bonedot_node.inputs["Texture Alpha"],
            tex_node.outputs["Alpha"],
            verify_limits=True,
        )
        node_tree.links.new(
            bonedot_node.outputs["BSDF"],
            output_node.inputs["Surface"],
            verify_limits=True,
        )

        tex_node.location = (0, 0)
        bonedot_node.location = (280, 0)
        output_node.location = (460, 0)
        mesh.materials.append(mat)
        return mat


# Import Mutiple Sprite
class Bonedot_OT_ImportSprites(bpy.types.Operator, ImportHelper):
    bl_idname = "bonedot.import_sprites"
    bl_label = "Import Sprites"
    bl_options = {"REGISTER", "UNDO"}

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    filepath: StringProperty(default="test")

    filter_image: BoolProperty(default=True, options={"HIDDEN", "SKIP_SAVE"})
    filter_movie: BoolProperty(default=True, options={"HIDDEN", "SKIP_SAVE"})
    filter_folder: BoolProperty(default=True, options={"HIDDEN", "SKIP_SAVE"})
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})
    replace: BoolProperty(name="Update Existing", default=True)

    def execute(self, context: Context):
        sprite_object = functions.get_sprite_object(context.active_object)
        ext = os.path.splitext(self.filepath)[1]
        folder = os.path.dirname(self.filepath)
        self.set_shading(context)

        context.scene.view_settings.view_transform = "Standard"
        for i in self.files:
            filepath = os.path.join(folder, i.name)
            if i.name not in bpy.data.objects:
                bpy.ops.bonedot.import_sprite(
                    path=filepath, parent=sprite_object.name, scale=1
                )
        return {"FINISHED"}

    def set_shading(self, context: Context):
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "RENDERED"
