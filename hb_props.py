"""
hb_props.py

Property group definitions for ModifiedHomeBuilder4.

This file defines HB_Asset_Handle: a registration-safe wrapper around asset
references. Historically addons sometimes used bpy.types.AssetHandle directly
in CollectionProperty definitions which is not suitable for registration in
Blender 5.0.0b. To remain compatible we provide a small PropertyGroup that
stores a reference to the underlying asset via a PointerProperty to an ID
block (the actual asset datablock).

We also provide a small container HB_Props with a CollectionProperty using
HB_Asset_Handle so existing code can keep storing asset references safely.
"""

import bpy
from bpy.props import (
    CollectionProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


class HB_Asset_Handle(bpy.types.PropertyGroup):
    """Registration-safe wrapper for an asset handle.

    Instead of using bpy.types.AssetHandle directly in CollectionProperty (which
    can't be used as a type for registration in Blender 5.0), we wrap an
    asset reference in a PropertyGroup. Here we store a reference to the
    asset datablock via a PointerProperty to bpy.types.ID. Addon code that
    previously used AssetHandle members can be adapted to read the stored
    ID datablock (e.g. .asset_handle).
    """

    # Store the actual asset datablock (any ID-based asset like an object, mesh, material...)
    asset_handle: PointerProperty(
        name="Asset Datablock",
        description="Reference to the asset's ID datablock (registration-safe)",
        type=bpy.types.ID,
    )

    # Optionally keep a label or path for convenience
    asset_name: StringProperty(
        name="Asset Name",
        description="Cached name of the referenced asset",
        default="",
    )


class HB_Props(bpy.types.PropertyGroup):
    """Container for addon properties. Includes a collection of HB_Asset_Handle.

    Other addon-wide properties can be added to this class. This keeps a
    single PointerProperty on WindowManager/Scene instead of many global
    top-level properties.
    """

    assets: CollectionProperty(
        name="HB Assets",
        type=HB_Asset_Handle,
        description="Collection of registration-safe asset handles",
    )

    active_asset_index: IntProperty(
        name="Active Asset Index",
        default=0,
    )


classes = (
    HB_Asset_Handle,
    HB_Props,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Attach a single property container to WindowManager so UI panels and
    # operators can access it via context.window_manager.hb_props
    if not hasattr(bpy.types.WindowManager, "hb_props"):
        bpy.types.WindowManager.hb_props = PointerProperty(type=HB_Props)


def unregister():
    # Remove the property from WindowManager first
    if hasattr(bpy.types.WindowManager, "hb_props"):
        delattr(bpy.types.WindowManager, "hb_props")

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
