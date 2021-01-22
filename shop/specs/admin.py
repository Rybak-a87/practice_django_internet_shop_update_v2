from django.contrib import admin

from .models import CategoryFeature, ProductFeatures, FeatureValidator


admin.site.register(CategoryFeature)
admin.site.register(ProductFeatures)
admin.site.register(FeatureValidator)
