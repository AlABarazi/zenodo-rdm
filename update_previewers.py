from invenio_app.factory import create_app
from pkg_resources import iter_entry_points

app = create_app()

print("Updating previewers configuration...")

with app.app_context():
    # Get the previewer extension
    from invenio_previewer.ext import InvenioPreviewer
    
    # Check if the extension exists
    previewer_ext = app.extensions.get('invenio-previewer')
    if not previewer_ext:
        print("Invenio-Previewer extension not found, initializing it...")
        previewer_ext = InvenioPreviewer(app)
        app.extensions['invenio-previewer'] = previewer_ext
    
    # Force registration of previewers
    print("Discovering and registering previewers...")
    for entry_point in iter_entry_points(group='invenio_previewer.previewers'):
        print(f"Found previewer: {entry_point.name}")
        module = entry_point.load()
        if not hasattr(module, 'can_preview') or not hasattr(module, 'preview'):
            print(f"ERROR: {entry_point.name} has no can_preview or preview functions")
            continue
        
        # Register the previewer
        previewer_ext.register_previewer(entry_point.name, module)
        print(f"Registered previewer: {entry_point.name}")
    
    # Print registered previewers
    print("\nRegistered previewers:")
    for name in previewer_ext.previewers:
        print(f" - {name}")
    
    # Update the configuration
    app.config['PREVIEWER_PREFERENCE'] = ['zenodo_image', 'pdfjs', 'simple_image', 'zip', 'csv_dthreejs', 'json_prismjs', 'simple_text', 'xml_json']
    print("\nPreviewer preferences:")
    print(app.config['PREVIEWER_PREFERENCE'])
    
    # Update IIIF configuration
    app.config['IIIF_PREVIEW_ENABLED'] = True
    app.config['RDM_RECORDS_MEDIA_FILES_ENABLED'] = True
    print("\nIIIF configuration updated.")
    
    # Try to get the tile processor
    try:
        from invenio_rdm_records.records.processors.tiles import TilesProcessor
        tile_processor = TilesProcessor()
        print("\nTiles processor found.")
    except ImportError as e:
        print(f"\nError importing TilesProcessor: {e}")
        
    # Reload entry points cache
    import importlib
    import site
    site.addsitedir(app.instance_path)
    importlib.invalidate_caches()
    
    print("\nReloaded entry points cache. Previewers should now be registered.") 