# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Additional views."""

from flask import Blueprint, current_app, g, render_template, jsonify
from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.resources.serializers import UIJSONSerializer
from invenio_records_resources.resources.records.utils import search_preference
from marshmallow import ValidationError

from .decorators import cached_unless_authenticated_or_flashes
from .filters import is_blr_related_record, is_verified_community, is_verified_record
from .support.support import ZenodoSupport


#
# Views
#
@cached_unless_authenticated_or_flashes(timeout=600, key_prefix="frontpage")
def frontpage_view_function():
    """Zenodo frontpage view."""
    recent_uploads = current_rdm_records.records_service.search(
        identity=g.identity,
        params={
            "sort": "newest",
            "size": 10,
            "q": current_app.config["ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY"],
        },
        search_preference=search_preference(),
        expand=False,
    )

    records_ui = []

    for record in recent_uploads:
        record_ui = UIJSONSerializer().dump_obj(record)
        records_ui.append(record_ui)

    featured_communities = current_communities.service.featured_search(
        identity=g.identity,
        params=None,
        search_preference=search_preference(),
    )

    return render_template(
        current_app.config["THEME_FRONTPAGE_TEMPLATE"],
        show_intro_section=current_app.config["THEME_SHOW_FRONTPAGE_INTRO_SECTION"],
        recent_uploads=records_ui,
        featured_communities=featured_communities,
    )


#
# Registration
#
def create_blueprint(app):
    """Create the ZenodoRDM blueprint."""
    blueprint = Blueprint(
        'zenodo_rdm',
        __name__,
        template_folder='templates',
        static_folder='static',
    )

    @blueprint.route('/zenodo')
    def index():
        """Zenodo landing page."""
        return render_template('zenodo_rdm/index.html')

    @app.errorhandler(ValidationError)
    def handle_validation_errors(e):
        if isinstance(e, ValidationError):
            dic = e.messages
            deserialized = []
            for error_tuple in dic.items():
                field, value = error_tuple
                deserialized.append({"field": field, "messages": value})
            return {"errors": deserialized}, 400
        return e.message, 400

    # Support URL rule
    support_endpoint = app.config["SUPPORT_ENDPOINT"] or "/support"
    blueprint.add_url_rule(
        support_endpoint,
        view_func=ZenodoSupport.as_view("support_form"),
        strict_slashes=False,
    )

    app.register_error_handler(400, handle_validation_errors)

    # Register template filters
    blueprint.add_app_template_filter(is_blr_related_record)
    blueprint.add_app_template_test(is_verified_record, name="verified_record")
    blueprint.add_app_template_test(is_verified_community, name="verified_community")

    # Add route for checking IIIF implementation
    @blueprint.route('/zenodo/check-iiif-for-pdf/<pid_value>')
    def check_iiif_for_pdf(pid_value):
        """Check IIIF implementation for PDF files."""
        import os
        import json
        import requests
        
        # Get the IIIF manifest for the record
        manifest_url = f"{current_app.config.get('SITE_UI_URL')}/api/iiif/record:{pid_value}/manifest"
        
        try:
            # Allow self-signed certificates for local development
            response = requests.get(manifest_url, verify=False)
            manifest = response.json()
            
            # Check if the manifest has any canvases
            sequence = manifest.get("sequences", [{}])[0]
            canvases = sequence.get("canvases", [])
            
            # Check the IIIF directory for PTIF files for this record
            images_dir = os.path.join(current_app.instance_path, "images", "public")
            
            # Check for PTIF files
            ptif_files = []
            for pattern_prefix in ["21", "20"]:
                dir_pattern = os.path.join(images_dir, pattern_prefix, "6_", "_")
                if os.path.exists(dir_pattern):
                    for filename in os.listdir(dir_pattern):
                        if filename.endswith(".ptif") and os.path.isfile(os.path.join(dir_pattern, filename)):
                            ptif_files.append({
                                "filename": filename,
                                "path": os.path.join(dir_pattern, filename),
                                "dir_pattern": pattern_prefix
                            })
            
            return jsonify({
                "manifest_url": manifest_url,
                "manifest": manifest,
                "canvas_count": len(canvases),
                "ptif_files": ptif_files
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "manifest_url": manifest_url
            }), 500

    return blueprint
