from django.urls import path
from . import views

app_name = 'youtubeapp'

urlpatterns = [
		path('',views.IndexView.as_view(), name='index'),
		path('post/', views.CreateMovieView.as_view(), name='post'),
		path('post_done/',
		views.PostSuccessView.as_view(),
		name='post_done'),
		path('movie/<int:category>',
		views.CategoryView.as_view(),
		name = 'movie_cat'
		),
		path('user-list/<int:user>',
		views.UserView.as_view(),
		name = 'user_list'
		),
		path('detail/<int:pk>',
		views.DetailView.as_view(),
		name = 'movie_detail'
		),
		path('mypage/',
		views.MypageView.as_view(),
		name = 'mypage'
		),
		path('movie/<int:pk>/delete/',
		views.MovieDeleteView.as_view(),
		name='movie_delete'),
] 