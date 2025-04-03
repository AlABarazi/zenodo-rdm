# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Extensions for ZenodoRDM."""

from flask import current_app

class ZenodoRDM:
    """ZenodoRDM extension."""

    def __init__(self, app=None):
        """Initialize extension."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        
        # Initialize the previewer extension
        from zenodo_rdm.previewer.ext import ZenodoPreviewerExt
        self.previewer = ZenodoPreviewerExt(app)
        
        app.extensions['zenodo-rdm'] = self
        
    def init_config(self, app):
        """Initialize configuration."""
        # Import config module
        try:
            import zenodo_rdm.config as config
            for k in dir(config):
                if k.startswith('ZENODO_'):
                    app.config.setdefault(k, getattr(config, k))
        except ImportError:
            app.logger.warning("Could not import zenodo_rdm.config") 