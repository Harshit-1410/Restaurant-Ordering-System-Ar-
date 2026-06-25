from django.contrib import admin
from .models import Restaurant, Category, MenuItem

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}  # auto-fills slug as you type name

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'order']
    list_filter = ['restaurant']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ['name', 'restaurant', 'category', 'price', 'is_veg', 'is_available', 'has_ar']
    list_filter   = ['restaurant', 'category', 'is_available', 'is_veg']
    search_fields = ['name']

    fieldsets = [
        (None, {
            'fields': ['restaurant', 'category', 'name', 'description', 'price', 'image', 'is_veg', 'is_available'],
        }),
        ('AR Models', {
            'fields': ['ar_model_file', 'ar_model_usdz'],
            'description': (
                'ar_model_file → .glb file (Android / Chrome / desktop 3D preview). '
                'ar_model_usdz → .usdz file (iOS Safari AR Quick Look).'
            ),
        }),
    ]

    @admin.display(boolean=True, description='AR?')
    def has_ar(self, obj):
        return obj.ar_has_model