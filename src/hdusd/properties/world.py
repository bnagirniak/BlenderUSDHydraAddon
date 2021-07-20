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

from . import HdUSDProperties


class WorldProperties(HdUSDProperties):
    bl_type = bpy.types.World

    enabled: bpy.props.BoolProperty(
        name="Enable Environment",
        description="Enable Environment Light",
        default=True
    )
    intensity: bpy.props.FloatProperty(
        name="Intensity",
        description="Environment intensity",
        min=0.0,
        default=1.0,
    )
    color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Color to use as a constant environment light",
        subtype='COLOR',
        min=0.0, max=1.0, size=3,
        default=(0.5, 0.5, 0.5)
    )
    image: bpy.props.PointerProperty(
        type=bpy.types.Image,
        name="Image"
    )
