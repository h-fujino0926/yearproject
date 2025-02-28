from django.db import models

from accounts.models import CustomUser

class Category(models.Model):
    title = models.CharField(
        verbose_name='カテゴリ',
        max_length=50
    )

    def __str__(self):
        return self.title

class YearMovie(models.Model):

    user = models.ForeignKey(
        CustomUser,
        verbose_name='ユーザー',
        on_delete=models.CASCADE
    )
    CATEGORY=(('dailylife','日常'),
              ('music','音楽'),
              ('game','ゲーム')
              )
    title = models.CharField(
        verbose_name='タイトル',
        max_length=50,
    )
    uptime_at = models.DateTimeField(
        verbose_name='投稿時間',
    )
    category = models.ForeignKey(
        Category,
        verbose_name='カテゴリ',
        max_length=50,
        choices=CATEGORY,
        on_delete=models.PROTECT
    )
    movie_file = models.ImageField(
        verbose_name='動画ファイル',
        max_length=200,
        default="",
        upload_to = 'media'
    )
    description = models.TextField(
        verbose_name='概要',
        max_length=300,
    )

    def __str__(self):
        return self.title

class MovieTagName(models.Model):
    name = models.CharField(max_length=200, default="")

class MovieTagList(models.Model):
    content = models.ForeignKey(YearMovie, on_delete=models.CASCADE)
    tag = models.ForeignKey(MovieTagName, on_delete=models.CASCADE)