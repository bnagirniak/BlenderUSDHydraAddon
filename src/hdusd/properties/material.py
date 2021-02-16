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
import bpy
import MaterialX as mx

from . import HdUSDProperties
from ..mx_nodes.node_tree import MxNodeTree
from ..bl_nodes.nodes import ShaderNodeOutputMaterial


class MaterialProperties(HdUSDProperties):
    bl_type = bpy.types.Material

    mx_node_tree: bpy.props.PointerProperty(type=MxNodeTree)

    def export(self) -> [mx.Document, None]:
        material = self.id_data
        output_node = next((node for node in material.node_tree.nodes if
                            node.bl_idname == ShaderNodeOutputMaterial.__name__), None)

        if not output_node:
            return None

        doc = mx.createDocument()
        doc.setVersionString("1.38")

        ShaderNodeOutputMaterial(doc, material, output_node, None, None).export()
        return doc
