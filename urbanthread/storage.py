"""Cloudinary-backed storage for Django ImageFields."""

from io import BytesIO
from pathlib import PurePosixPath
from uuid import uuid4

import cloudinary.uploader
import cloudinary.utils
import requests
from django.core.files import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class CloudinaryMediaStorage(Storage):
    """Store uploaded images in Cloudinary and serve them from its CDN."""

    def _save(self, name, content):
        path = PurePosixPath(name)
        folder = '' if str(path.parent) == '.' else path.parent.as_posix()
        public_id = f'{path.stem}_{uuid4().hex}'
        if hasattr(content, 'seek'):
            content.seek(0)

        result = cloudinary.uploader.upload(
            content,
            folder=folder,
            public_id=public_id,
            resource_type='image',
            overwrite=False,
            unique_filename=False,
        )

        stored_public_id = result['public_id']
        file_format = result.get('format') or path.suffix.lstrip('.') or 'jpg'
        return f'{stored_public_id}.{file_format}'

    def _open(self, name, mode='rb'):
        response = requests.get(self.url(name), timeout=30)
        response.raise_for_status()
        return File(BytesIO(response.content), name=name)

    def _public_id_and_format(self, name):
        path = PurePosixPath(name)
        if path.suffix:
            return path.with_suffix('').as_posix(), path.suffix.lstrip('.')
        return path.as_posix(), None

    def url(self, name):
        public_id, file_format = self._public_id_and_format(name)
        return cloudinary.utils.cloudinary_url(
            public_id,
            format=file_format,
            secure=True,
        )[0]

    def delete(self, name):
        public_id, _file_format = self._public_id_and_format(name)
        cloudinary.uploader.destroy(public_id, resource_type='image', invalidate=True)

    def exists(self, name):
        # _save adds a UUID, so names are unique without a remote API lookup.
        return False
