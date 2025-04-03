from invenio_app.factory import create_app
from pkg_resources import iter_entry_points

app = create_app()
print('Checking registered previewers:')

with app.app_context():
    from invenio_previewer.ext import InvenioPreviewer
    previewer_ext = app.extensions.get('invenio-previewer', None)
    
    # Force registration of previewers if needed
    if not previewer_ext:
        print("Invenio-Previewer extension not found, initializing it...")
        previewer_ext = InvenioPreviewer(app)
        app.extensions['invenio-previewer'] = previewer_ext
    
    # Force registration of previewers
    print("Discovering previewers from entry points...")
    for entry_point in iter_entry_points(group='invenio_previewer.previewers'):
        print(f"Found previewer entry point: {entry_point.name} -> {entry_point.module_name}")
        if entry_point.name not in previewer_ext.previewers:
            module = entry_point.load()
            if hasattr(module, 'can_preview') and hasattr(module, 'preview'):
                previewer_ext.register_previewer(entry_point.name, module)
                print(f"Registered previewer: {entry_point.name}")
            else:
                print(f"Entry point {entry_point.name} missing can_preview or preview function")
    
    if previewer_ext:
        print("\nRegistered previewers after initialization:", list(previewer_ext.previewers.keys()))
        
        # Check IIIF configuration
        print("\nIIIF Configuration:")
        print(f"IIIF_PREVIEW_ENABLED: {app.config.get('IIIF_PREVIEW_ENABLED', False)}")
        print(f"RDM_RECORDS_MEDIA_FILES_ENABLED: {app.config.get('RDM_RECORDS_MEDIA_FILES_ENABLED', False)}")
        
        # Check specifically for image previewers
        for previewer_name in ['zenodo_image', 'image_previewer']:
            if previewer_name in previewer_ext.previewers:
                print(f"\n{previewer_name} is registered!")
                
        # Check preview preferences
        print("\nPreviewer Preferences:")
        print(app.config.get('PREVIEWER_PREFERENCE', []))
        
        # Check module imports
        print("\nTrying to import the zenodo_rdm.previewer module:")
        try:
            import zenodo_rdm.previewer.image_previewer as imp
            print(f"Module imported successfully: {imp}")
            print(f"can_preview function exists: {hasattr(imp, 'can_preview')}")
            print(f"preview function exists: {hasattr(imp, 'preview')}")
        except ImportError as e:
            print(f"Import error: {e}")
    else:
        print("No previewers registered") 