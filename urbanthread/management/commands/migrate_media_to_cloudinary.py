from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage

from urbanthread.storage import CloudinaryMediaStorage


class Command(BaseCommand):
    help = 'Upload existing local ImageField files to Cloudinary and update their database paths.'

    def handle(self, *args, **options):
        if not isinstance(default_storage, CloudinaryMediaStorage):
            raise CommandError('Set CLOUDINARY_URL before running this command.')

        media_root = Path(settings.MEDIA_ROOT).resolve()
        uploaded = 0
        skipped = 0

        for model in apps.get_models():
            if model._meta.abstract or model._meta.proxy or model._meta.auto_created:
                continue
            image_fields = [
                field for field in model._meta.get_fields()
                if getattr(field, 'get_internal_type', lambda: None)() == 'ImageField'
                and getattr(field, 'concrete', False)
            ]
            if not image_fields:
                continue

            for instance in model.objects.all().iterator():
                for field in image_fields:
                    image = getattr(instance, field.name)
                    if not image or not image.name:
                        continue

                    local_path = (media_root / image.name).resolve()
                    if not local_path.is_relative_to(media_root) or not local_path.is_file():
                        skipped += 1
                        continue

                    with local_path.open('rb') as source:
                        image.save(Path(image.name).name, ContentFile(source.read()), save=False)
                    instance.save(update_fields=[field.name])
                    uploaded += 1
                    self.stdout.write(f'Uploaded {model._meta.label} #{instance.pk} — {field.name}')

        self.stdout.write(self.style.SUCCESS(f'Finished: {uploaded} uploaded, {skipped} skipped.'))
