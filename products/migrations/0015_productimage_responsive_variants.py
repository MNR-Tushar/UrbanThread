from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import migrations, models
from PIL import Image, ImageOps


def create_existing_responsive_images(apps, schema_editor):
    ProductImage = apps.get_model('products', 'ProductImage')
    database = schema_editor.connection.alias
    for product_image in ProductImage.objects.using(database).exclude(image='').iterator(chunk_size=100):
        try:
            with product_image.image.open('rb') as source:
                original = ImageOps.exif_transpose(Image.open(source))
                if original.mode not in ('RGB', 'RGBA'):
                    original = original.convert('RGBA' if 'transparency' in original.info else 'RGB')
                stem = Path(product_image.image.name).stem
                for field_name, max_size in (('image_small', (480, 480)), ('image_medium', (960, 960))):
                    variant = original.copy()
                    variant.thumbnail(max_size, Image.Resampling.LANCZOS)
                    output = BytesIO()
                    variant.save(output, format='WEBP', quality=82, method=6)
                    getattr(product_image, field_name).save(
                        f'{stem}_{max_size[0]}.webp', ContentFile(output.getvalue()), save=False,
                    )
            product_image.save(update_fields=['image_small', 'image_medium'])
        except (OSError, ValueError):
            # Unreadable or unsupported legacy files remain available at their original URL.
            continue


class Migration(migrations.Migration):
    dependencies = [('products', '0014_product_average_rating_product_review_count')]

    operations = [
        migrations.AddField(
            model_name='productimage', name='image_small',
            field=models.ImageField(blank=True, editable=False, upload_to='product_images/optimized/'),
        ),
        migrations.AddField(
            model_name='productimage', name='image_medium',
            field=models.ImageField(blank=True, editable=False, upload_to='product_images/optimized/'),
        ),
        migrations.RunPython(create_existing_responsive_images, migrations.RunPython.noop),
    ]
