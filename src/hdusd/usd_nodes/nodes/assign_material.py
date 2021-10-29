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


MAX_MESH_COUNT = 10
MIN_MESH_COUNT = 1

DUMMY_MESH_NAME = 'NONE'


def get_meshes(stage):
    usd_prims = (prim for prim in stage.TraverseAll() if prim.GetTypeName() == 'Mesh')
    mesh_collection = [(DUMMY_MESH_NAME, DUMMY_MESH_NAME, DUMMY_MESH_NAME)]

    for prim in usd_prims:
        mesh_collection.append(
            (prim.GetPath().pathString, prim.GetName(), str(len(mesh_collection))))

    return mesh_collection


class HDUSD_USD_NODETREE_MT_assign_material_material_base_class(bpy.types.Menu):
    bl_idname = "HDUSD_USD_NODETREE_MT_assign_material_material_base_class"
    bl_label = "Material"

    index = 0

    def draw(self, context):
        layout = self.layout
        materials = (material for material in bpy.data.materials if not material.is_grease_pencil)

        for mat in materials:
            row = layout.row()
            op = row.operator(HDUSD_USD_NODETREE_OP_assign_material_assign_material.bl_idname,
                              text=mat.name_full, icon='MATERIAL')
            op.material_prop_name = "material_" + str(self.index)
            op.material_name = mat.name_full


class HDUSD_USD_NODETREE_OP_assign_material_assign_material(bpy.types.Operator):
    """Assign material"""
    bl_idname = "hdusd.usd_nodetree_assign_material_assign_material"
    bl_label = ""

    material_prop_name: bpy.props.StringProperty(default="")
    material_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        setattr(context.node, self.material_prop_name, bpy.data.materials[self.material_name])
        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_assign_material_remove_material(bpy.types.Operator):
    """Remove material"""
    bl_idname = "hdusd.usd_nodetree_assign_material_remove_material"
    bl_label = ""

    material_prop_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        setattr(context.node, self.material_prop_name, None)
        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_assign_material_add_mesh(bpy.types.Operator):
    """Add mesh"""
    bl_idname = "hdusd.usd_nodetree_assign_material_add_mesh"
    bl_label = ""

    def execute(self, context):
        mesh_idxs_vector = context.node.mesh_idxs_vector

        not_selected_meshes = next((idx for idx in mesh_idxs_vector if idx == -1), None)

        if not not_selected_meshes:
            return {"FINISHED"}

        for i, index in enumerate(mesh_idxs_vector):
            if i == len(mesh_idxs_vector):
                mesh_idxs_vector[i] = i
                return {"FINISHED"}

            if mesh_idxs_vector[i] == -1:
                mesh_idxs_vector[i] = i
                return {"FINISHED"}

        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_assign_material_remove_mesh(bpy.types.Operator):
    """Add mesh"""
    bl_idname = "hdusd.usd_nodetree_assign_material_remove_mesh"
    bl_label = ""

    index: bpy.props.IntProperty()

    def execute(self, context):
        mesh_idxs_vector = context.node.mesh_idxs_vector

        current_material_prop_name = context.node.material_collection_names[self.index]
        current_mesh_prop_name = context.node.mesh_collection_names[self.index]

        setattr(context.node, current_material_prop_name, None)
        setattr(context.node, current_mesh_prop_name, DUMMY_MESH_NAME)

        selected_meshes = len(tuple(filter(lambda val: val != -1, mesh_idxs_vector)))
        if selected_meshes == MIN_MESH_COUNT:
            return {"FINISHED"}

        mesh_idxs_vector[self.index] = -1
        return {"FINISHED"}


class AssignMaterialNode(USDNode):
    """Assign material"""
    bl_idname = 'usd.AssignMaterial'
    bl_label = "Assign material"
    bl_icon = "MATERIAL"

    mesh_collection_names = tuple(f"mesh_collection_{i}" for i in range(MAX_MESH_COUNT))
    material_collection_names = tuple(f"material_{i}" for i in range(MAX_MESH_COUNT))

    def update_data(self, context):
        self.reset()

    def get_mesh_collection(self, context):
        input_stage = self.get_input_link('Input')
        if not input_stage or not context:
            return ()

        return get_meshes(input_stage)

    # region properties
    mesh_idxs_vector: bpy.props.IntVectorProperty(
        name="Selected meshes", size=MAX_MESH_COUNT,
        default=tuple((i for i in range(MIN_MESH_COUNT))) +
                tuple((-1 for i in range(MAX_MESH_COUNT - MIN_MESH_COUNT)))
    )

    mesh_collection_0: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data,
    )

    material_0: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_1: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data,
    )

    material_1: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_2: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_2: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_3: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_3: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_4: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_4: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_5: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_5: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_6: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_6: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_7: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_7: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_8: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_8: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )

    mesh_collection_9: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data
    )

    material_9: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data
    )
    # endregion

    def draw_buttons(self, context, layout):
        layout.operator(HDUSD_USD_NODETREE_OP_assign_material_add_mesh.bl_idname)

        selected_meshes = tuple(idx for idx in self.mesh_idxs_vector if idx != -1)

        for i in selected_meshes:
            mesh_prop_name = "mesh_collection_" + str(i)
            material_prop_name = "material_" + str(i)

            material_prop_value = getattr(self, material_prop_name)

            split = layout.row(align=True).split(factor=0.85)
            col = split.column()
            col.prop(self, mesh_prop_name)
            col = split.column()
            op_remove_mesh = col.operator(
                HDUSD_USD_NODETREE_OP_assign_material_remove_mesh.bl_idname, icon='X')
            op_remove_mesh.index = i

            split = layout.row(align=True).split(factor=0.85)
            col = split.column()
            menu_name = "HDUSD_USD_NODETREE_MT_assign_material_" + material_prop_name
            if material_prop_value:
                col.menu(menu_name, text=material_prop_value.name_full, icon='MATERIAL')
                col = split.column()
                op_remove_mat = col.operator(HDUSD_USD_NODETREE_OP_assign_material_remove_material.bl_idname, icon='X')
                op_remove_mat.material_prop_name = material_prop_name
            else:
                col.menu(menu_name, text=" ", icon='MATERIAL')
                split.column()

            layout.separator()

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return None

        cached_stage = self.cached_stage.create()
        cached_stage.GetRootLayer().TransferContent(input_stage.GetRootLayer())

        selected_meshes = tuple(idx for idx in self.mesh_idxs_vector if idx != -1)

        for i in selected_meshes:
            mesh_prop_name = "mesh_collection_" + str(i)

            mesh_prop_value = getattr(self, mesh_prop_name)
            material_prop_value = getattr(self, self.material_collection_names[i])

            if not mesh_prop_value or mesh_prop_value == DUMMY_MESH_NAME:
                continue

            usd_mesh_prim = cached_stage.GetPrimAtPath(mesh_prop_value)
            if not usd_mesh_prim or not usd_mesh_prim.IsValid():
                continue

            usd_prim = cached_stage.GetPrimAtPath(mesh_prop_value).GetParent()
            usd_mesh = UsdGeom.Mesh.Get(cached_stage, mesh_prop_value)
            usd_mesh_rel_mat = UsdShade.MaterialBindingAPI.Get(cached_stage, usd_mesh.GetPath()).GetDirectBindingRel()

            old_mat_path = next((target for target in usd_mesh_rel_mat.GetTargets()), None) \
                if usd_mesh_rel_mat.IsValid() else None

            old_mat_prim = cached_stage.GetPrimAtPath(old_mat_path) if old_mat_path else None

            old_mat_parent_prim = old_mat_prim.GetParent().GetParent() \
                if old_mat_prim and old_mat_prim.IsValid() else None

            if old_mat_parent_prim and old_mat_parent_prim.IsValid():
                old_mat_parent_prim.SetActive(False)
                cached_stage.RemovePrim(old_mat_parent_prim.GetPath())

            if material_prop_value:
                usd_material = material.sync(usd_prim, material_prop_value, None)
                UsdShade.MaterialBindingAPI(usd_mesh).Bind(usd_material)

        return cached_stage
