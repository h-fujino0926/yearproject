from django.forms import ModelForm
from .models import YearMovie

class YearMovieForm(ModelForm):
    class Meta:
        model = YearMovie
        fields = ['category','title','description','movie_file']