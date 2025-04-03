from flask import current_app
from invenio_app.factory import create_app

app = create_app()
with app.app_context():
    # Check IIIF configurations
    print("Checking IIIF configuration...")
    print(f"RDM_RECORDS_MEDIA_FILES_ENABLED: {current_app.config.get('RDM_RECORDS_MEDIA_FILES_ENABLED', False)}")
    print(f"IIIF_PREVIEW_ENABLED: {current_app.config.get('IIIF_PREVIEW_ENABLED', False)}")
    print(f"PREVIEW_MAX_FILE_SIZE: {current_app.config.get('PREVIEW_MAX_FILE_SIZE', 'N/A')}")
    print(f"PREVIEW_EXTENSIONS: {current_app.config.get('PREVIEW_EXTENSIONS', [])}")
    print(f"PREVIEW_MIME_TYPES: {current_app.config.get('PREVIEW_MIME_TYPES', [])}")
    
    # Check Mirador configuration
    print("\nChecking Mirador configuration...")
    print(f"RDM_RECORDS_UI_FILES_PREVIEW_IIIF_MIRADOR_BASE_TEMPLATE: {current_app.config.get('RDM_RECORDS_UI_FILES_PREVIEW_IIIF_MIRADOR_BASE_TEMPLATE', 'N/A')}")
    print(f"IIIF_FORMATS: {current_app.config.get('IIIF_FORMATS', {})}")
    
    # Check UI preview settings
    print("\nChecking UI preview settings...")
    rdm_extension = current_app.extensions.get('invenio-rdm-records', None)
    if rdm_extension:
        service_config = getattr(rdm_extension, 'service_records_config', None)
        if service_config:
            print(f"Has service config: Yes")
            print(f"Media files enabled: {getattr(service_config, 'media_files_enabled', False)}")
            print(f"Default media files enabled: {getattr(service_config, 'default_media_files_enabled', False)}")
        else:
            print(f"Has service config: No")
    else:
        print("RDM extension not found")
    
    # Check storage paths
    print("\nChecking storage paths...")
    iiif_path = current_app.config.get('IIIF_STORAGE_PATH', 'N/A')
    print(f"IIIF storage path: {iiif_path}")
    
    import os
    if iiif_path != 'N/A' and os.path.exists(iiif_path):
        print(f"IIIF storage path exists: Yes")
        print(f"IIIF storage path contents: {os.listdir(iiif_path)}")
    else:
        print(f"IIIF storage path exists: No or not accessible")
    
    # Check for processors
    print("\nChecking processors...")
    try:
        from invenio_rdm_records.services.config import RDMFilesServiceConfig
        print(f"RDMFilesServiceConfig available: Yes")
        
        from invenio_rdm_records.services.iiif import ImageProcessor, TilesProcessor
        print(f"IIIF processors imported successfully")
    except ImportError as e:
        print(f"Import error: {e}")
    
    # Check for file previewers
    print("\nChecking file previewers...")
    try:
        from invenio_previewer.ext import InvenioPreviewer
        previewer_ext = current_app.extensions.get('invenio-previewer', None)
        if previewer_ext:
            print(f"Registered previewers: {list(previewer_ext.previewers.keys())}")
            
            # Check for PDF and TIF previewers
            pdf_previewer = previewer_ext.previewers.get('pdfjs', None)
            if pdf_previewer:
                print(f"PDF.js previewer: Found")
            else:
                print(f"PDF.js previewer: Not found")
                
            iiif_previewer = previewer_ext.previewers.get('iiif', None)
            if iiif_previewer:
                print(f"IIIF previewer: Found")
            else:
                print(f"IIIF previewer: Not found")
    except ImportError as e:
        print(f"Import error for previewers: {e}")
        
    print("\nConfiguration check complete.") 