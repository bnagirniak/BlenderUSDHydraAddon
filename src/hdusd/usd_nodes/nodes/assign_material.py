# **********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ********************************************************************
import bpy
import math

from pxr import Usd, UsdGeom, Tf, UsdShade

from .base_node import USDNode

from ...export import material
from ...properties import CachedStageProp


MAX_MESH_COUNT = 10


def get_meshes(stage):
    usd_prims = (prim for prim in stage.TraverseAll() if prim.GetTypeName() == 'Mesh')
    mesh_collection = []

    for prim in usd_prims:
        mesh_collection.append(
            (str(len(mesh_collection)), prim.GetName(), prim.GetPath().pathString))

    return mesh_collection


class HDUSD_USD_NODETREE_OP_assign_material_add_mesh(bpy.types.Operator):
    """Add mesh"""
    bl_idname = "hdusd.usd_nodetree_assign_material_add_mesh"
    bl_label = ""

    def execute(self, context):
        if len(context.node.mesh_with_material) < MAX_MESH_COUNT:
            context.node.mesh_with_material.add()

        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_assign_material_remove_mesh(bpy.types.Operator):
    """Add mesh"""
    bl_idname = "hdusd.usd_nodetree_assign_material_remove_mesh"
    bl_label = ""

    index: bpy.props.IntProperty()

    def execute(self, context):
        context.node.mesh_with_material.remove(self.index)
        return {"FINISHED"}


class MeshWithMaterialItem(bpy.types.PropertyGroup):
    def update_data(self, context):
        current_node = self.get_current_node(context)
        current_node.reset()

    def get_current_node(self, context):
        node_tree = context.space_data.node_tree if context.space_data.tree_type == 'hdusd.USDTree' else None
        return node_tree.nodes["Assign material"]

    def get_mesh_collection(self, context):
        if not hasattr(context.space_data, "tree_type"):
            return tuple((("NONE", "None", "", 1),))

        current_node = self.get_current_node(context)
        cached_stage = current_node.cached_stage() if current_node else None

        return get_meshes(cached_stage) if cached_stage else tuple((("NONE", "None", "", 1),))

    def get_valid_material(self, object):
        return not object.is_grease_pencil

    mesh: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="Select material",
        poll=get_valid_material,
        update=update_data
    )


class AssignMaterialNode(USDNode):
    """Assign material"""
    bl_idname = 'usd.AssignMaterial'
    bl_label = "Assign material"
    bl_icon = "MATERIAL"

    def update_data(self, context):
        self.reset()

    mesh_with_material: bpy.props.CollectionProperty(type=MeshWithMaterialItem)

    cached_stage: bpy.props.PointerProperty(type=CachedStageProp)

    def draw_buttons(self, context, layout):
        if not hasattr(context.space_data, "tree_type"):
            return

        layout.operator(HDUSD_USD_NODETREE_OP_assign_material_add_mesh.bl_idname)

        index = 0

        for mesh in self.mesh_with_material:

            split = layout.row(align=True).split(factor=0.85)
            col = split.column()
            col.prop(mesh, "mesh")
            col = split.column()
            row = col.row(align=True)
            op_remove_mesh = row.operator(HDUSD_USD_NODETREE_OP_assign_material_remove_mesh.bl_idname, icon='X')
            op_remove_mesh.index = index
            index += 1
            layout.prop(mesh, "material")

            layout.separator()

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return None

        cached_stage = self.cached_stage.create()
        cached_stage.GetRootLayer().TransferContent(input_stage.GetRootLayer())

        if len(self.mesh_with_material) == 1 and self.mesh_with_material[0].mesh == 'NONE':
            return cached_stage

        for mesh in self.mesh_with_material:
            if not mesh.material or not bool(mesh.mesh) or mesh.mesh == 'NONE':
                continue

            selected_mesh = get_meshes(cached_stage)[int(mesh.mesh)]
            usd_prim = cached_stage.GetPrimAtPath(selected_mesh[2]).GetParent()
            usd_mesh = UsdGeom.Mesh.Get(cached_stage, selected_mesh[2])

            usd_mesh_rel_mat = UsdShade.MaterialBindingAPI.Get(cached_stage, usd_mesh.GetPath()).GetDirectBindingRel()

            old_mat_path = next((target for target in usd_mesh_rel_mat.GetTargets()), None) \
                if usd_mesh_rel_mat.IsValid() else None

            old_mat_parent_prim = cached_stage.GetPrimAtPath(old_mat_path).GetParent().GetParent() \
                if old_mat_path else None

            if old_mat_parent_prim and old_mat_parent_prim.IsValid():
                old_mat_parent_prim.SetActive(False)
                cached_stage.RemovePrim(old_mat_parent_prim.GetPath())

            usd_material = material.sync(usd_prim, mesh.material, None)
            UsdShade.MaterialBindingAPI(usd_mesh).Bind(usd_material)

        return cached_stage
