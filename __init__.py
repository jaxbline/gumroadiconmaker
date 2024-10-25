bl_info = {
    "name": "Gumroad Icon Maker",
    "author": "Jax",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Jax's Stuff",
    "description": "Im lazy and want to make icons for Gumroad",
    "category": "3D View",
}

import bpy
import os
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import PointerProperty, CollectionProperty
from bpy.utils import register_class, unregister_class
import math

class IconMakerObjectItem(PropertyGroup):
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
        description="Object to be parented to the Spinner"
    )

class JAXSTUFF_OT_add_object(Operator):
    bl_idname = "jaxstuff.add_object"
    bl_label = "Add Object"
    bl_description = "Add a new object slot"
    
    def execute(self, context):
        context.scene.icon_maker_objects.add()
        return {'FINISHED'}

class JAXSTUFF_OT_remove_object(Operator):
    bl_idname = "jaxstuff.remove_object"
    bl_label = "Remove"
    bl_description = "Remove this object slot"
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        context.scene.icon_maker_objects.remove(self.index)
        return {'FINISHED'}

class JAXSTUFF_PT_icon_maker(Panel):
    bl_label = "Icon Maker"
    bl_idname = "JAXSTUFF_PT_icon_maker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Jax's Stuff"
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Objects to Parent:")
        for i, item in enumerate(context.scene.icon_maker_objects):
            row = layout.row(align=True)
            row.prop(item, "object", text="")
            remove_op = row.operator(JAXSTUFF_OT_remove_object.bl_idname, text="", icon='X')
            remove_op.index = i
        
        layout.operator(JAXSTUFF_OT_add_object.bl_idname, text="Add Object", icon='ADD')
        layout.separator()
        layout.operator("jaxstuff.import_icon_maker", text="Setup Icon")

class JAXSTUFF_OT_import_icon_maker(Operator):
    bl_idname = "jaxstuff.import_icon_maker"
    bl_label = "Setup Icon"
    bl_description = "Import the IconMaker collection and configure render settings"
    
    def execute(self, context):
        addon_dir = os.path.dirname(os.path.realpath(__file__))
        blend_file = os.path.join(addon_dir, "iconmaker.blend")
        
        try:
            with bpy.data.libraries.load(blend_file, link=False) as (data_from, data_to):
                if "IconMaker" in data_from.collections:
                    data_to.collections = ["IconMaker"]
                else:
                    self.report({'ERROR'}, "IconMaker collection not found in the blend file")
                    return {'CANCELLED'}
            
            imported_collection = None
            for coll in data_to.collections:
                if coll is not None:
                    if coll.name not in bpy.context.scene.collection.children:
                        bpy.context.scene.collection.children.link(coll)
                    imported_collection = coll
            
            spinner = None
            if imported_collection:
                for obj in imported_collection.objects:
                    if obj.name == "Spinner":
                        spinner = obj
                        break
            
            if spinner:
                for item in context.scene.icon_maker_objects:
                    if item.object:
                        orig_location = item.object.location.copy()
                        
                        item.object.parent = spinner
                        
                        item.object.location = orig_location
                
                scene = bpy.context.scene
                
                if spinner.animation_data:
                    spinner.animation_data_clear()
                
                spinner.rotation_mode = 'XYZ'
                
                scene.frame_set(1)
                spinner.rotation_euler.z = 0
                spinner.keyframe_insert(data_path="rotation_euler", frame=1, index=2)
                
                scene.frame_set(60)
                spinner.rotation_euler.z = math.radians(360)
                spinner.keyframe_insert(data_path="rotation_euler", frame=60, index=2)
                
                for fcurve in spinner.animation_data.action.fcurves:
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'LINEAR'
                        keyframe.easing = 'AUTO'
                
                scene.frame_set(1)
                
            else:
                self.report({'WARNING'}, "Spinner object not found in imported collection")
            
            scene = bpy.context.scene
            
            scene.render.engine = 'BLENDER_EEVEE_NEXT'
            
            scene.eevee.use_raytracing = True
            scene.eevee.taa_render_samples = 128
            
            scene.render.resolution_x = 720
            scene.render.resolution_y = 720
            scene.render.resolution_percentage = 100
            
            scene.render.fps = 24
            scene.frame_start = 1
            scene.frame_end = 60
            
            scene.render.film_transparent = True
            
            scene.render.image_settings.file_format = 'PNG'
            scene.render.image_settings.color_mode = 'RGBA'
            scene.render.image_settings.color_depth = '8'
            scene.render.image_settings.compression = 50
            
            scene.use_nodes = True
            tree = scene.node_tree
            
            for node in tree.nodes:
                tree.nodes.remove(node)
                
            render_layer = tree.nodes.new('CompositorNodeRLayers')
            render_layer.location = (-300, 0)
            
            glare_node = tree.nodes.new('CompositorNodeGlare')
            glare_node.location = (0, 0)
            glare_node.glare_type = 'FOG_GLOW'
            
            composite = tree.nodes.new('CompositorNodeComposite')
            composite.location = (300, 0)
            
            tree.links.new(render_layer.outputs['Image'], glare_node.inputs['Image'])
            tree.links.new(glare_node.outputs['Image'], composite.inputs['Image'])
            
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces[0].shading.type = 'RENDERED'
                    area.spaces[0].shading.use_compositor = 'ALWAYS'
            
            scene.use_nodes = True
            scene.render.use_compositing = True
            
            self.report({'INFO'}, "Successfully imported IconMaker collection and configured render settings")
                    
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

classes = (
    IconMakerObjectItem,
    JAXSTUFF_OT_add_object,
    JAXSTUFF_OT_remove_object,
    JAXSTUFF_PT_icon_maker,
    JAXSTUFF_OT_import_icon_maker
)

def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.icon_maker_objects = CollectionProperty(type=IconMakerObjectItem)

def unregister():
    del bpy.types.Scene.icon_maker_objects
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()