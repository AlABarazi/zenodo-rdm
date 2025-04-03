"""Extension module configuration for previewers."""

from pathlib import Path
import importlib
import os
import pkg_resources
from flask import current_app


class ZenodoPreviewerExt:
    """Zenodo previewer extension."""

    def __init__(self, app=None):
        """Initialize extension."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize application."""
        self.configure_iiif(app)
        app.extensions['zenodo-previewer'] = self

    def configure_iiif(self, app):
        """Configure IIIF settings."""
        # Configure IIIF settings
        app.config['IIIF_PREVIEW_ENABLED'] = True
        app.config['RDM_RECORDS_MEDIA_FILES_ENABLED'] = True
        
        # Ensure zenodo_image has priority
        app.config['PREVIEWER_PREFERENCE'] = [
            'zenodo_image', 'image_previewer', 'pdfjs', 'simple_image', 'xml_json', 
            'json_prismjs', 'simple_text', 'csv_dthreejs', 'zip'
        ]
        
        # Define the IIIF storage path
        instance_path = app.instance_path
        iiif_path = os.path.join(instance_path, 'images')
        if not os.path.exists(iiif_path):
            os.makedirs(iiif_path, exist_ok=True)
        
        app.config['IIIF_STORAGE_PATH'] = iiif_path
        
        # Configure Mirador settings
        app.config['MIRADOR_PREVIEW_EXTENSIONS'] = [
            'pdf', 'jpg', 'jpeg', 'png', 'gif', 'tif', 'tiff'
        ]
        
        # Configure IIIF formats
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
        
        # Log the configuration setup
        app.logger.info("IIIF configuration complete.") 