# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""IIIF extension for ZenodoRDM."""

from flask import current_app


class ZenodoIIIFExt:
    """ZenodoRDM IIIF extension."""

    def __init__(self, app=None):
        """Initialize extension."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize application."""
        self.apply_iiif_manifest_patch(app)
        app.extensions['zenodo-iiif'] = self

    def apply_iiif_manifest_patch(self, app):
        """Apply the IIIF manifest patch."""
        # Import here to avoid circular imports
        from zenodo_rdm.iiif.manifest import patch_iiif_manifest
        
        with app.app_context():
            try:
                patch_iiif_manifest()
                app.logger.info("ZenodoRDM IIIF manifest enhancement applied successfully")
            except Exception as e:
                app.logger.error(f"Failed to apply IIIF manifest enhancement: {str(e)}") 