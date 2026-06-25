# restaurants/models.py

from django.db import models


def _ar_storage():
    """
    AR model files (.glb / .usdz) are always stored on the local filesystem.

    They are committed to git (media/ar_models/) so they are present on every
    Railway deploy without needing any external storage service.
    Django serves them via the permanent /media/ route in urls.py.

    Food images use DEFAULT_FILE_STORAGE (Supabase / S3 when configured) but
    AR files intentionally bypass that so their URLs are always /media/ar_models/…
    regardless of which cloud backend is active.
    """
    from django.core.files.storage import FileSystemStorage
    return FileSystemStorage()


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)  # used in QR code URL
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)  # for sorting categories on menu

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.restaurant.name} — {self.name}"


class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name='menu_items', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    ar_model_file = models.FileField(upload_to='ar_models/', blank=True, null=True, storage=_ar_storage)   # .glb  — Android / WebXR / desktop 3D
    ar_model_usdz = models.FileField(upload_to='ar_models/', blank=True, null=True, storage=_ar_storage)   # .usdz — iOS Safari AR Quick Look
    is_veg = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def ar_has_model(self):
        return bool(self.ar_model_file or self.ar_model_usdz)

    def __str__(self):
        return f"{self.name} — ₹{self.price}"