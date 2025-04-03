from invenio_app.factory import create_app

app = create_app()
print('Checking IIIF and Mirador configuration:')

with app.app_context():
    # Check IIIF configuration
    print(f"IIIF_PREVIEW_ENABLED: {app.config.get('IIIF_PREVIEW_ENABLED', False)}")
    print(f"RDM_RECORDS_MEDIA_FILES_ENABLED: {app.config.get('RDM_RECORDS_MEDIA_FILES_ENABLED', False)}")
    
    # Check Mirador configuration
    print(f"MIRADOR_PREVIEW_EXTENSIONS: {app.config.get('MIRADOR_PREVIEW_EXTENSIONS', [])}")
    print(f"RDM_RECORDS_UI_FILES_PREVIEW_IIIF_MIRADOR_BASE_TEMPLATE: {app.config.get('RDM_RECORDS_UI_FILES_PREVIEW_IIIF_MIRADOR_BASE_TEMPLATE', 'N/A')}")
    
    # Check previewer preference
    print(f"PREVIEWER_PREFERENCE: {app.config.get('PREVIEWER_PREFERENCE', [])}")
    
    # Check IIIF formats
    print(f"IIIF_FORMATS: {app.config.get('IIIF_FORMATS', {})}")
    
    # Check for the zenodo-previewer extension
    print(f"zenodo-previewer extension loaded: {'zenodo-previewer' in app.extensions}")
    
    # Try importing the image_previewer module
    try:
        import zenodo_rdm.previewer.image_previewer as imp
        print(f"Image previewer module: {imp}")
        print(f"can_preview function exists: {hasattr(imp, 'can_preview')}")
        print(f"preview function exists: {hasattr(imp, 'preview')}")
        
        # Check the is_pdf_previewable function
        if hasattr(imp, 'is_pdf_previewable'):
            print(f"is_pdf_previewable function exists: {hasattr(imp, 'is_pdf_previewable')}")
        
        # Check for tiles processing config
        from invenio_rdm_records.services.iiif.tasks import generate_tiles
        print(f"generate_tiles function exists: {generate_tiles}")
    except ImportError as e:
        print(f"Import error: {e}")
    
    # Check IIIF storage path
    iiif_path = app.config.get('IIIF_STORAGE_PATH', 'N/A')
    print(f"IIIF storage path: {iiif_path}")
    
    import os
    if iiif_path != 'N/A' and os.path.exists(iiif_path):
        print(f"IIIF storage path exists: Yes")
        print(f"IIIF storage path contents: {os.listdir(iiif_path)}")
    else:
        print(f"IIIF storage path exists: No or not accessible") 