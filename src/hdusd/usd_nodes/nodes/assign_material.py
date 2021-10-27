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


class HDUSD_USD_NODETREE_OP_assign_material_assign_material(bpy.types.Operator):
    """Assign material"""
    bl_idname = "hdusd.usd_nodetree_assign_material_assign_material"
    bl_label = ""

    material_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.node.material = bpy.data.materials[self.material_name]
        return {"FINISHED"}


class HDUSD_USD_NODETREE_MT_assign_material_material(bpy.types.Menu):
    bl_idname = "HDUSD_USD_NODETREE_MT_assign_material_material"
    bl_label = "Material"

    def draw(self, context):
        layout = self.layout
        materials = (material for material in bpy.data.materials if not material.is_grease_pencil)

        for material in materials:
            row = layout.row()
            op = row.operator(HDUSD_USD_NODETREE_OP_assign_material_assign_material.bl_idname,
                              text=material.name_full, icon='MATERIAL')
            op.material_name = material.name_full


class HDUSD_USD_NODETREE_OP_assign_material_remove_material(bpy.types.Operator):
    """Remove material"""
    bl_idname = "hdusd.usd_nodetree_assign_material_remove_material"
    bl_label = ""

    def execute(self, context):
        context.node.material = None
        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_assign_material_add_mesh(bpy.types.Operator):
    """Add mesh"""
    bl_idname = "hdusd.usd_nodetree_assign_material_add_mesh"
    bl_label = ""

    def execute(self, context):
        context.node.mesh_count += 1
        context.node.mesh_with_material.add()
        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_assign_material_remove_mesh(bpy.types.Operator):
    """Add mesh"""
    bl_idname = "hdusd.usd_nodetree_assign_material_remove_mesh"
    bl_label = ""

    def execute(self, context):
        return {"FINISHED"}


class MeshWithMaterialItem(bpy.types.PropertyGroup):
    def get_mesh_collection(self, context):
        node_tree = context.space_data.node_tree if context.space_data.tree_type == 'hdusd.USDTree' else None
        assign_material_node = node_tree.nodes["Assign material"]
        cached_stage = assign_material_node.cached_stage()

        return get_meshes(cached_stage) if cached_stage else ()

    def get_valid_material(self, object):
        return not object.is_grease_pencil

    mesh_collection: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
    )

    material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        poll=get_valid_material
    )


class AssignMaterialNode(USDNode):
    """Assign material"""
    bl_idname = 'usd.AssignMaterial'
    bl_label = "Assign material"
    bl_icon = "MATERIAL"

    def update_data(self, context):
        self.reset()

    mesh_count: bpy.props.IntProperty(
        name="Inputs",
        min=1, max=MAX_MESH_COUNT, default=1,
    )

    mesh_with_material: bpy.props.CollectionProperty(type=MeshWithMaterialItem)

    cached_stage: bpy.props.PointerProperty(type=CachedStageProp)

    def draw_buttons(self, context, layout):
        layout.operator(HDUSD_USD_NODETREE_OP_assign_material_add_mesh.bl_idname)

        for mesh in self.mesh_with_material:
            layout.prop(mesh, "mesh_collection")
            layout.prop(mesh, "material")

            layout.separator()

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return None

        stage = self.cached_stage.create()
        stage.GetRootLayer().TransferContent(input_stage.GetRootLayer())

        #if not self.mesh_collection:
        #    return stage

        #selected_mesh = get_meshes(stage)[int(self.mesh_collection)]
        #usd_prim = stage.GetPrimAtPath(selected_mesh[2]).GetParent()
        #usd_mesh = UsdGeom.Mesh.Get(stage, selected_mesh[2])

        #usd_mesh_rel_mat = UsdShade.MaterialBindingAPI.Get(stage, usd_mesh.GetPath()).GetDirectBindingRel()

        #old_mat_path = next((target for target in usd_mesh_rel_mat.GetTargets()), None) \
        #    if usd_mesh_rel_mat.IsValid() else None

        #old_mat_parent_prim = stage.GetPrimAtPath(old_mat_path).GetParent().GetParent() \
        #    if old_mat_path else None

        #if old_mat_parent_prim and old_mat_parent_prim.IsValid():
        #    old_mat_parent_prim.SetActive(False)
        #    stage.RemovePrim(old_mat_parent_prim.GetPath())

        #usd_material = material.sync(usd_prim, self.material, None)
        #UsdShade.MaterialBindingAPI(usd_mesh).Bind(usd_material)

        return stage
