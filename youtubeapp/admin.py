from django.contrib import admin
from .models import Category, YearMovie
# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','title')
    list_display_links = ('id','title')

admin.site.register(Category,CategoryAdmin)

class YearMovieAdmin(admin.ModelAdmin):
    list_display = ('id','title')
    list_display_links = ('id','title')

admin.site.register(YearMovie,YearMovieAdmin)

class YearMovieAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'upload_date')
    list_display_links = ('id', 'title', 'upload_date')

class MovieTagListAdmin(admin.ModelAdmin):
    list_display = ('content', 'tag')
    list_display_linsk = ('content', 'tag')

class MovieTagNameAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_display_links = ('name',)