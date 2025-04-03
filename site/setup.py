# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo RDM setup file."""

from setuptools import setup

setup(
    entry_points={
        'invenio_base.apps': [
            'zenodo_rdm = zenodo_rdm.ext:ZenodoRDM',
        ],
        'invenio_base.api_apps': [
            'zenodo_rdm = zenodo_rdm.ext:ZenodoRDM',
        ],
        'invenio_base.blueprints': [
            'zenodo_rdm = zenodo_rdm.views:create_blueprint',
        ],
        'invenio_assets.webpack': [
            'zenodo_rdm_theme = zenodo_rdm.webpack:theme',
        ],
        'invenio_config.module': [
            'zenodo_rdm = zenodo_rdm.config',
        ],
        'invenio_i18n.translations': [
            'messages = zenodo_rdm',
        ],
        'flask.commands': [],
        'invenio_previewer.previewers': [
            'zenodo_image = zenodo_rdm.previewer.image_previewer',
        ],
    },
)
