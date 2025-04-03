# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo RDM previewers."""

from .image_previewer import can_preview, preview

__all__ = ('can_preview', 'preview') 