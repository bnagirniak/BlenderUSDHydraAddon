#**********************************************************************
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
#********************************************************************
from concurrent import futures
import threading

import bpy

from . import HdUSDProperties

from ..utils import matlib


class MatlibProperties(bpy.types.PropertyGroup):
    pcoll = None

    def get_materials(self):
        return matlib.manager.get_materials(
            category_id=self.category if self.category != 'ALL' else '',
            search_str=self.search.strip().lower()
        )

    def get_materials_prop(self, context):
        return [(mat.id, mat.title, mat.full_description, mat.renders[0].thumbnail_icon_id, i)
                for i, mat in enumerate(self.get_materials())]

    def get_categories_prop(self, context):
        categories = [('ALL', "All Categories", "Show materials for all categories")]
        categories += ((cat.id, cat.title, f"Category: {cat.title}")
                       for cat in matlib.manager.get_categories())
        return categories

    def update_material(self, context):
        materials = self.get_materials()
        if materials and self.material not in materials:
            self.material = materials[0].id
            self.package_id = self.pcoll.materials[self.material].packages[0].id

    material: bpy.props.EnumProperty(
        name="Material",
        description="Select material",
        items=get_materials_prop,
    )
    category: bpy.props.EnumProperty(
        name="Category",
        description="Select materials category",
        items=get_categories_prop,
        update=update_material,
    )
    search: bpy.props.StringProperty(
        name="Search",
        description="Search materials by title",
        update=update_material,
    )
    package_id: bpy.props.StringProperty(
        name="Package id",
        description="Selected material package"
    )

    @classmethod
    def register(cls):
        import bpy.utils.previews
        cls.pcoll = bpy.utils.previews.new()
        cls.pcoll.materials = None
        cls.pcoll.categories = None
        matlib.manager.load_data(cls.pcoll)

    @classmethod
    def unregister(cls):
        bpy.utils.previews.remove(cls.pcoll)


class WindowManagerProperties(HdUSDProperties):
    bl_type = bpy.types.WindowManager

    matlib: bpy.props.PointerProperty(type=MatlibProperties)
