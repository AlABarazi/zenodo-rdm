from setuptools import setup

setup(
    name='iiif-previewer',
    version='0.1.0',
    description='IIIF and Mirador Preview Extension for InvenioRDM',
    packages=['iiif_extension'],
    entry_points={
        'invenio_base.apps': [
            'iiif_previewer = iiif_extension.ext:IIIFPreviewerExt',
        ],
    },
) 