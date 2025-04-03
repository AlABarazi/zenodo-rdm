"""Extension module configuration for IIIF and Mirador."""

from flask import Blueprint
from invenio_previewer.config import PREVIEWER_PREFERENCE as BASE_PREFERENCE
import os

class IIIFPreviewerExt:
    """IIIF and Mirador extension for InvenioRDM."""

    def __init__(self, app=None):
        """Initialize extension."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize application."""
        self.init_config(app)
        app.extensions['iiif-previewer'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Define the IIIF storage path
        instance_path = app.instance_path
        iiif_path = os.path.join(instance_path, 'images')
        if not os.path.exists(iiif_path):
            os.makedirs(iiif_path, exist_ok=True)
        
        # Enable IIIF and set configuration
        app.config['IIIF_PREVIEW_ENABLED'] = True
        app.config['IIIF_STORAGE_PATH'] = iiif_path
        
        # Register IIIF previewer with higher preference than pdfjs and simple_image
        preference = list(BASE_PREFERENCE)
        
        # Add 'iiif' before 'pdfjs' if it exists
        if 'pdfjs' in preference:
            pdfjs_idx = preference.index('pdfjs')
            preference.insert(pdfjs_idx, 'iiif')
        else:
            preference.append('iiif')
        
        # Update configuration
        app.config['PREVIEWER_PREFERENCE'] = preference
        
        # Make sure media files are enabled
        app.config['RDM_RECORDS_MEDIA_FILES_ENABLED'] = True
        
        # Set Mirador base template
        app.config['RDM_RECORDS_UI_FILES_PREVIEW_IIIF_MIRADOR_BASE_TEMPLATE'] = 'invenio_app_rdm/record_detail.html'
        
        # Define preview extensions and mime types
        app.config['PREVIEW_EXTENSIONS'] = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'tif', 'tiff']
        app.config['PREVIEW_MIME_TYPES'] = [
            'application/pdf',
            'image/jpeg', 
            'image/jpg', 
            'image/png', 
            'image/gif', 
            'image/tiff'
        ]
        
        # Configure the IIIF image format available
        app.config['IIIF_FORMATS'] = {
            'pdf': 'application/pdf',
            'gif': 'image/gif',
            'jp2': 'image/jp2',
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'tif': 'image/tiff',
            'tiff': 'image/tiff',
        }
        
        # Update service configuration if possible
        try:
            for ext_name, ext in app.extensions.items():
                if 'invenio-rdm-records' in ext_name:
                    if hasattr(ext, 'service_records'):
                        service = ext.service_records
                        if hasattr(service, '_config'):
                            if hasattr(service._config, 'media_files_enabled'):
                                service._config.media_files_enabled = True
                            if hasattr(service._config, 'default_media_files_enabled'):
                                service._config.default_media_files_enabled = True
        except Exception as e:
            app.logger.warning(f"Failed to update service configuration: {str(e)}")
        
        print("IIIF and Mirador configuration applied successfully!") 