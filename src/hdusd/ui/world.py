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

from cycles.ui import panel_node_draw

from . import HdUSD_Panel


class HDUSD_WORLD_PT_preview(HdUSD_Panel):
    bl_label = "Preview"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.world and super().poll(context)

    def draw(self, context):
        self.layout.template_preview(context.world)


class HDUSD_WORLD_PT_environment(HdUSD_Panel):
    bl_label = "Environment Light"
    bl_context = 'world'

    @classmethod
    def poll(cls, context):
        return context.world and super().poll(context)

    def draw_header(self, context):
        self.layout.prop(context.scene.world.rpr, 'enabled', text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        rpr = context.scene.world.rpr

        layout.enabled = rpr.enabled

        layout.prop(rpr, 'intensity')
        layout.separator()

        row = layout.row()
        row.use_property_split = False
        row.prop(rpr, 'mode', expand=True)

        if rpr.mode == 'IBL':
            ibl = rpr.ibl

            layout.template_ID(ibl, "image", open="image.open")

            row = layout.row()
            row.enabled = ibl.image is None
            row.prop(ibl, 'color')

        else:
            sun_sky = rpr.sun_sky

            col = layout.column(align=True)
            col.prop(sun_sky, 'azimuth')
            col.prop(sun_sky, 'altitude')

            layout.prop(sun_sky, 'resolution')

        row = layout.row()
        row.prop(rpr, 'group')
