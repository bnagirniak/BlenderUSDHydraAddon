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
import MaterialX as mx

import bpy


def prettify_string(str):
    return str.replace('_', ' ').title()


class MxNode(bpy.types.ShaderNode):
    """Base node from which all MaterialX nodes will be made"""
    bl_compatibility = {'HdUSD'}
    bl_icon = 'MATERIAL'
    bl_label = 'mx'

    # holds the materialx nodedef object
    mx_nodedef: mx.NodeDef

    def init(self, context):
        ''' generates inputs and outputs from ones specified '''
        for mx_input in self.mx_nodedef.getInputs():
            name = mx_input.getName()
            input = self.inputs.new(name=prettify_string(name), type='mx.NodeSocket')
            if hasattr(self, name.lower()):
                input.property_name = name.lower()

        for output in self.mx_nodedef.getOutputs():
            name = output.getName()
            self.outputs.new(name=prettify_string(name), type='mx.NodeSocket')

    def draw_buttons(self, context, layout):
        for mx_param in self.mx_nodedef.getParameters():
            layout.prop(self, mx_param.getName())

    @classmethod
    def poll(cls, ntree):
        if hasattr(ntree, 'bl_idname'):
            return ntree.bl_idname == 'mx.NodeTree'
        else:
            return True

    @staticmethod
    def import_from_mx(nt, mx_node: mx.Node):
        ''' creates a node from a Mx node spec
            sets the params and inputs based on spec '''

        try:
            node_type = 'mx.' + mx_node.getCategory()
            blender_node = nt.nodes.new(node_type)
            blender_node.label = mx_node.getName()
            # get params from
            return blender_node
        except:
            # TODO custom nodedefs in file
            return None


def parse_value(mx_type, val_str, only_first=False):
    val = None
    if mx_type == 'float':
        val = float(val_str)
    elif mx_type.startswith('color') or mx_type.startswith('vector') and 'array' not in mx_type:
        val = [float(x) for x in val_str.split(',')]
    elif mx_type == 'string':
        val = val_str
    elif mx_type == 'integer':
        val = int(val_str)
    elif mx_type == 'filename':
        val = val_str
    elif mx_type == 'boolean':
        val = val_str.lower() == 'true'

    if only_first and isinstance(val, list):
        val = val[0]

    return val


def get_param(mx_param):
    ''' convert a mx param into a blender property '''
    mx_param_type = mx_param.getType()
    name = mx_param.getName()
    prop_attrs = {
        'name': prettify_string(name)
    }

    # handle ui attrs:
    if mx_param.hasValueString():
        prop_attrs['default'] = parse_value(mx_param_type, mx_param.getValueString())
    if mx_param.hasAttribute('uimin'):
        prop_attrs['min'] = parse_value(mx_param_type, mx_param.getAttribute('uimin'),
                                        only_first=True)
    if mx_param.hasAttribute('uimax'):
        prop_attrs['max'] = parse_value(mx_param_type, mx_param.getAttribute('uimax'),
                                        only_first=True)
    if mx_param.hasAttribute('uisoftmin'):
        prop_attrs['soft_min'] = parse_value(mx_param_type, mx_param.getAttribute('uisoftmin'),
                                             only_first=True)
    if mx_param.hasAttribute('uisoftmax'):
        prop_attrs['soft_max'] = parse_value(mx_param_type, mx_param.getAttribute('uisoftmax'),
                                             only_first=True)

    if mx_param_type == 'float':
        return bpy.props.FloatProperty, prop_attrs

    elif mx_param_type.startswith('color'):
        prop_attrs['size'] = int(mx_param_type[-1])
        prop_attrs['subtype'] = 'COLOR'
        return bpy.props.FloatVectorProperty, prop_attrs

    elif mx_param_type == 'string':
        return bpy.props.StringProperty, prop_attrs

    elif mx_param_type == 'integer':
        return bpy.props.IntProperty, prop_attrs

    elif mx_param_type == 'filename':
        prop_attrs['subtype'] = 'FILE_NAME'
        return bpy.props.StringProperty, prop_attrs

    elif mx_param_type == 'boolean':
        return bpy.props.BoolProperty, prop_attrs

    elif mx_param_type.startswith('vector') and 'array' not in mx_param_type:
        prop_attrs['size'] = int(mx_param_type[-1])
        prop_attrs['subtype'] = 'XYZ'
        return bpy.props.FloatVectorProperty, prop_attrs

    else:
        raise TypeError('unknown type', mx_param_type)


def create_node_type(mx_nodedef):
    ''' Create Subtype MxNode for this node def
        The parameters and inputs of the node def are saved as Blender properties
    '''
    data = {
        'bl_label': prettify_string(mx_nodedef.getNodeString()),
        'bl_idname': "hdusd.mx_" + mx_nodedef.getNodeString(),
        'mx_nodedef': mx_nodedef
    }

    # properties are stored as annotations on the custom type
    annotations = {}
    for mx_param in mx_nodedef.getParameters():
        annotations[mx_param.getName()] = get_param(mx_param)
    for mx_input in mx_nodedef.getInputs():
        created_property = get_param(mx_input)
        if created_property is not None:
            annotations[mx_input.getName()] = created_property

    if len(annotations):
        data['__annotations__'] = annotations

    node_type = type(mx_nodedef.getNodeString(), (MxNode,), data)
    return node_type