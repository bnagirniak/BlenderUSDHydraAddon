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
import re

from pxr import Usd, UsdGeom, Tf, UsdShade

from .base_node import USDNode

from ...export import material

MAX_VISIBLE_MESHES = 2


class AssignMaterialNode(USDNode):
    """Assign material"""
    bl_idname = 'usd.AssignMaterial'
    bl_label = "Assign material"
    bl_icon = "MATERIAL"
    bl_width_default = 300

    def update_data(self, context):
        self.reset()

    def get_mesh_collection(self, context):
        input_stage = self.get_input_link('Input')
        if not input_stage:
            return ()

        if self.filter_path:
            # creating search regex pattern and getting filtered rpims
            prog = re.compile(self.filter_path.replace('*', '#')  # temporary replacing '*' to '#'
                              .replace('/', '\/')  # for correct regex pattern
                              .replace('##', '[\w\/]*')  # creation
                              .replace('#', '\w*'))

            prims_path = tuple(prim_path for prim in input_stage.TraverseAll()
                               if prog.fullmatch((prim_path := str(prim.GetPath())))
                               and prim.GetTypeName() == 'Mesh')
        else:
            prims_path = (str(prim.GetPath()) for prim in input_stage.TraverseAll() if prim.GetTypeName() == 'Mesh')

        mesh_collection = [('NONE', "", "")]

        for prim_path in prims_path:
            if len(mesh_collection) - 1 == MAX_VISIBLE_MESHES:
                mesh_collection.append(('...', '...', 'Use filter to see more available meshes'))
                return mesh_collection

            mesh_collection.append((prim_path, prim_path, prim_path))

        return mesh_collection

    def set_mesh(self, value):
        selected_mesh = self.get_mesh_collection(None)[value][0]
        self["filter_path"] = selected_mesh if selected_mesh not in ('...', 'NONE') else ''


    def poll_material(self, mat):
        return not mat.is_grease_pencil

    mesh: bpy.props.EnumProperty(
        name="Mesh",
        description="Select mesh",
        items=get_mesh_collection,
        update=update_data, set=set_mesh
    )

    material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        name="Material",
        description="",
        update=update_data,
        poll=poll_material
    )

    filter_path: bpy.props.StringProperty(
        name="Pattern",
        description="USD Path pattern. Use special characters means:\n"
                    "  * - any word or subword\n"
                    "  ** - several words separated by '/' or subword",
        default='/*',
        update=update_data
    )

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "mesh", text="", icon_only=True, icon='OUTLINER_DATA_MESH')
        row.separator()
        row.prop(self, 'filter_path', text="")
        row.separator()
        row.prop(self, "material", text="")

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return None

        cached_stage = self.cached_stage.create()
        cached_stage.GetRootLayer().TransferContent(input_stage.GetRootLayer())

        # creating search regex pattern and getting filtered rpims
        prog = re.compile(self.filter_path.replace('*', '#')  # temporary replacing '*' to '#'
                          .replace('/', '\/')  # for correct regex pattern
                          .replace('##', '[\w\/]*')  # creation
                          .replace('#', '\w*'))

        prims_path = tuple(prim_path for prim in input_stage.TraverseAll()
                           if prog.fullmatch((prim_path := str(prim.GetPath())))
                           and prim.GetTypeName() == 'Mesh')
        if not prims_path:
            return cached_stage

        material_prop_value = self.material

        for prim_path in prims_path:
            usd_mesh_prim = cached_stage.GetPrimAtPath(prim_path)
            if not usd_mesh_prim or not usd_mesh_prim.IsValid():
                continue

            usd_prim = cached_stage.GetPrimAtPath(prim_path).GetParent()
            usd_mesh = UsdGeom.Mesh.Get(cached_stage, prim_path)
            usd_mesh_rel_mat = UsdShade.MaterialBindingAPI.Get(cached_stage,
                                                               usd_mesh.GetPath()).GetDirectBindingRel()

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
