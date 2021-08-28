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
from pathlib import Path

import bpy

from .base_node import MxNode


class MxNode_HDUSD_mx_file(MxNode):
    bl_label = 'MaterialX File'
    bl_idname = 'hdusd.MxNode_mx_file'
    bl_description = "Import MaterialX (.mtlx) file"

    category = 'material'

    def update_prop(self, context):
        nodetree = self.id_data
        nodetree.update_()

    p_file: bpy.props.StringProperty(
        name="File",
        description="MaterialX (.mtlx) file",
        subtype="FILE_PATH",
        update=update_prop
    )

    def init(self, context):
        pass

    def draw_buttons(self, context, layout):
        layout.prop(self, 'p_file')

    def compute(self, out_key, **kwargs):
        return Path(self.p_file)


mx_node_classes = [MxNode_HDUSD_mx_file]
