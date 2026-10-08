bl_info = {
    "name": "Studio Backdrop & Light Rig",
    "author": "Your Name",
    "version": (1, 1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar (N) > Studio Setup",
    "description": "Fitted cyclorama, 100mm camera, live color/light controls, and 360 turntable.",
    "category": "Lighting",
}

import bpy
import math
from mathutils import Vector


# ------------------------------------------------------------------------
# 1. LIVE PROPERTY UPDATE CALLBACKS
# ------------------------------------------------------------------------

def update_backdrop_color(self, context):
    """Dynamically updates the cyclorama shader color in real time."""
    mat = bpy.data.materials.get("M_Studio_Backdrop")
    if mat and mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf and "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = self.backdrop_color


def update_backdrop_roughness(self, context):
    """Dynamically updates the cyclorama roughness in real time."""
    mat = bpy.data.materials.get("M_Studio_Backdrop")
    if mat and mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf and "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = self.backdrop_roughness


def update_light_multiplier(self, context):
    """Scales all studio lights relative to their stored base energy."""
    mult = self.light_intensity
    for light in bpy.data.lights:
        if "base_energy" in light:
            light.energy = light["base_energy"] * mult


# ------------------------------------------------------------------------
# 2. SCENE PROPERTY GROUP
# ------------------------------------------------------------------------

class StudioSettings(bpy.types.PropertyGroup):
    backdrop_color: bpy.props.FloatVectorProperty(
        name="Backdrop Color",
        description="Color of the seamless cyclorama wall",
        subtype='COLOR',
        default=(0.78, 0.78, 0.80, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        update=update_backdrop_color,
    )
    backdrop_roughness: bpy.props.FloatProperty(
        name="Roughness",
        description="Surface roughness (matte vs reflective sweep)",
        default=0.85,
        min=0.0,
        max=1.0,
        update=update_backdrop_roughness,
    )
    light_intensity: bpy.props.FloatProperty(
        name="Light Intensity",
        description="Master multiplier for all 3 studio lights",
        default=1.0,
        min=0.05,
        max=5.0,
        update=update_light_multiplier,
    )


# ------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# ------------------------------------------------------------------------

def create_light(name, light_type, energy, size, location, target_empty, collection, multiplier):
    """Creates an area light, tags its base energy, and tracks to empty."""
    light_data = bpy.data.lights.new(name=name, type=light_type)
    light_data["base_energy"] = energy
    light_data.energy = energy * multiplier
    light_data.size = size

    light_obj = bpy.data.objects.new(name=name, object_data=light_data)
    light_obj.location = location
    collection.objects.link(light_obj)

    constraint = light_obj.constraints.new(type='TRACK_TO')
    constraint.target = target_empty
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    return light_obj


def get_or_create_backdrop_material(color, roughness):
    """Creates or updates the neutral studio backdrop material."""
    mat_name = "M_Studio_Backdrop"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


# ------------------------------------------------------------------------
# 4. OPERATORS
# ------------------------------------------------------------------------

class OBJECT_OT_generate_studio(bpy.types.Operator):
    """Generate cyclorama, 3-point light rig, and 100mm camera"""
    bl_idname = "object.generate_studio"
    bl_label = "Generate Studio Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'MESH'
            and context.mode == 'OBJECT'
        )

    def execute(self, context):
        target = context.active_object
        props = context.scene.studio_props

        # 1. Bounding dimensions
        bbox = [target.matrix_world @ Vector(corner) for corner in target.bound_box]
        min_x = min(v.x for v in bbox)
        max_x = max(v.x for v in bbox)
        min_y = min(v.y for v in bbox)
        max_y = max(v.y for v in bbox)
        min_z = min(v.z for v in bbox)
        max_z = max(v.z for v in bbox)

        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        center_z = (min_z + max_z) / 2.0
        target_center = Vector((center_x, center_y, center_z))

        obj_width = max(max_x - min_x, 1.0)
        obj_depth = max(max_y - min_y, 1.0)
        obj_height = max(max_z - min_z, 1.0)
        max_dim = max(obj_width, obj_depth, obj_height)

        # 2. Collection
        col_name = f"Studio_Rig_{target.name}"
        rig_col = bpy.data.collections.get(col_name)
        if not rig_col:
            rig_col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(rig_col)

        # 3. Aim Empty
        empty_obj = bpy.data.objects.new(f"{target.name}_AimTarget", None)
        empty_obj.empty_display_type = 'PLAIN_AXES'
        empty_obj.empty_display_size = max_dim * 0.4
        empty_obj.location = target_center
        rig_col.objects.link(empty_obj)

        # 4. Backdrop Geometry
        cam_dist = max_dim * 5.5
        cyc_w = max(max_dim * 10.0, cam_dist * 1.6)
        cyc_front = center_y - (cam_dist + max_dim * 2.0)
        cyc_back = center_y + (max_dim * 5.0)
        cyc_top = min_z + (max_dim * 5.0)

        verts = [
            Vector((center_x - cyc_w / 2, cyc_front, min_z)),
            Vector((center_x + cyc_w / 2, cyc_front, min_z)),
            Vector((center_x + cyc_w / 2, cyc_back,  min_z)),
            Vector((center_x - cyc_w / 2, cyc_back,  min_z)),
            Vector((center_x - cyc_w / 2, cyc_back,  cyc_top)),
            Vector((center_x + cyc_w / 2, cyc_back,  cyc_top)),
        ]
        faces = [
            (0, 1, 2, 3),
            (3, 2, 5, 4),
        ]

        mesh_data = bpy.data.meshes.new(f"{target.name}_CycMesh")
        mesh_data.from_pydata(verts, [], faces)
        mesh_data.update()

        for poly in mesh_data.polygons:
            poly.use_smooth = True

        cyc_obj = bpy.data.objects.new(f"{target.name}_Backdrop", mesh_data)
        rig_col.objects.link(cyc_obj)

        bevel = cyc_obj.modifiers.new(name="Curvature", type='BEVEL')
        bevel.width = max_dim * 1.8
        bevel.segments = 16
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = 1.05

        mat = get_or_create_backdrop_material(props.backdrop_color, props.backdrop_roughness)
        if cyc_obj.data.materials:
            cyc_obj.data.materials[0] = mat
        else:
            cyc_obj.data.materials.append(mat)

        # 5. 3-Point Light Rig
        light_dist = max_dim * 3.0
        base_power = max(light_dist * light_dist * 17.5, 50.0)

        key_pos = Vector((
            center_x - light_dist * 0.8,
            center_y - light_dist * 0.8,
            center_z + light_dist * 0.9
        ))
        key_light = create_light(
            name=f"{target.name}_Key_Light",
            light_type='AREA',
            energy=base_power * 1.6,
            size=max_dim * 1.2,
            location=key_pos,
            target_empty=empty_obj,
            collection=rig_col,
            multiplier=props.light_intensity
        )
        key_light.data.color = (1.0, 0.97, 0.92)

        fill_pos = Vector((
            center_x + light_dist * 0.9,
            center_y - light_dist * 0.6,
            center_z + light_dist * 0.4
        ))
        fill_light = create_light(
            name=f"{target.name}_Fill_Light",
            light_type='AREA',
            energy=base_power * 0.6,
            size=max_dim * 1.8,
            location=fill_pos,
            target_empty=empty_obj,
            collection=rig_col,
            multiplier=props.light_intensity
        )
        fill_light.data.color = (0.92, 0.95, 1.0)

        rim_pos = Vector((
            center_x + light_dist * 0.6,
            center_y + light_dist * 0.9,
            center_z + light_dist * 1.1
        ))
        rim_light = create_light(
            name=f"{target.name}_Rim_Light",
            light_type='AREA',
            energy=base_power * 1.4,
            size=max_dim * 0.8,
            location=rim_pos,
            target_empty=empty_obj,
            collection=rig_col,
            multiplier=props.light_intensity
        )

        # 6. 100mm Camera
        cam_data = bpy.data.cameras.new(f"{target.name}_Camera_Data")
        cam_data.lens = 100.0
        cam_data.dof.use_dof = True
        cam_data.dof.focus_object = empty_obj
        cam_data.dof.aperture_fstop = 4.0

        cam_pos = Vector((center_x, center_y - cam_dist, center_z + (max_dim * 0.15)))
        cam_obj = bpy.data.objects.new(f"{target.name}_Camera_100mm", cam_data)
        cam_obj.location = cam_pos
        rig_col.objects.link(cam_obj)

        cam_track = cam_obj.constraints.new(type='TRACK_TO')
        cam_track.target = empty_obj
        cam_track.track_axis = 'TRACK_NEGATIVE_Z'
        cam_track.up_axis = 'UP_Y'

        context.scene.camera = cam_obj
        self.report({'INFO'}, f"Studio setup created for '{target.name}'")
        return {'FINISHED'}


class OBJECT_OT_create_turntable(bpy.types.Operator):
    """Add a seamless 120-frame 360-degree turntable animation to the active object"""
    bl_idname = "object.create_turntable"
    bl_label = "Add 360° Turntable (120 Frames)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.mode == 'OBJECT'
        )

    def execute(self, context):
        target = context.active_object

        # Set timeline range
        context.scene.frame_start = 1
        context.scene.frame_end = 120

        # Preserve starting orientation
        start_rot_z = target.rotation_euler.z

        # Temporarily force new keyframes to LINEAR interpolation during creation
        pref = context.preferences.edit
        orig_interp = pref.keyframe_new_interpolation_type
        pref.keyframe_new_interpolation_type = 'LINEAR'

        try:
            # Keyframe 1: Start
            target.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

            # Keyframe 121: 360-degree rotation (frame 121 ensures frame 120 isn't duplicate)
            target.rotation_euler.z = start_rot_z + math.radians(360.0)
            target.keyframe_insert(data_path="rotation_euler", index=2, frame=121)

            # Return object to initial rotation
            target.rotation_euler.z = start_rot_z
        finally:
            # Restore user's original keyframe preference
            pref.keyframe_new_interpolation_type = orig_interp

        # Universal fallback pass: handles legacy actions and modern layered actions
        if target.animation_data and target.animation_data.action:
            action = target.animation_data.action
            curves = []

            # Legacy actions
            if hasattr(action, "fcurves"):
                curves.extend(action.fcurves)

            # Modern Slotted / Layered actions
            if hasattr(action, "layers"):
                for layer in getattr(action, "layers", []):
                    for strip in getattr(layer, "strips", []):
                        for bag in getattr(strip, "channelbags", []):
                            if hasattr(bag, "fcurves"):
                                curves.extend(bag.fcurves)

            for fcurve in curves:
                if getattr(fcurve, "data_path", "") == "rotation_euler" and getattr(fcurve, "array_index", -1) == 2:
                    for kf in getattr(fcurve, "keyframe_points", []):
                        kf.interpolation = 'LINEAR'

        context.scene.frame_set(1)
        self.report({'INFO'}, f"Seamless turntable loop generated for '{target.name}'")
        return {'FINISHED'}


# ------------------------------------------------------------------------
# 5. SIDEBAR UI PANEL
# ------------------------------------------------------------------------

class VIEW3D_PT_studio_panel(bpy.types.Panel):
    bl_label = "Studio Setup"
    bl_idname = "VIEW3D_PT_studio_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Studio Setup"

    def draw(self, context):
        layout = self.layout
        props = context.scene.studio_props
        target = context.active_object

        # Main Setup Section
        box = layout.box()
        if target and target.type == 'MESH':
            box.label(text=f"Target: {target.name}", icon='OBJECT_DATA')
            box.operator("object.generate_studio", text="Generate Studio Rig", icon='LIGHT_SUN')
        else:
            box.label(text="Select a Mesh Object first", icon='INFO')

        # Live Material Tweaks
        mat_box = layout.box()
        mat_box.label(text="Backdrop Material", icon='MATERIAL')
        mat_box.prop(props, "backdrop_color", text="")
        mat_box.prop(props, "backdrop_roughness", slider=True)

        # Live Lighting Intensity
        light_box = layout.box()
        light_box.label(text="Master Lighting", icon='LIGHT')
        light_box.prop(props, "light_intensity", text="Intensity", slider=True)

        # Turntable Animation
        anim_box = layout.box()
        anim_box.label(text="Portfolio Showcase", icon='ANIM')
        anim_box.operator("object.create_turntable", text="Add 360° Turntable", icon='TIME')


# ------------------------------------------------------------------------
# 6. REGISTRATION
# ------------------------------------------------------------------------

classes = (
    StudioSettings,
    OBJECT_OT_generate_studio,
    OBJECT_OT_create_turntable,
    VIEW3D_PT_studio_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.studio_props = bpy.props.PointerProperty(type=StudioSettings)


def unregister():
    del bpy.types.Scene.studio_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()