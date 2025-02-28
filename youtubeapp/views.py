from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView,CreateView,DeleteView,ListView,DetailView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy,reverse
from .forms import YearMovieForm
from .models import YearMovie
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django import forms
from django.core.files.storage import default_storage, FileSystemStorage
from django.utils import timezone
from django.conf import settings
import ffmpeg
from django.db.models import Count
from .models import YearMovie, MovieTagList, MovieTagName
# Create your views here.

DATA_DIR = settings.MEDIA_ROOT + 'media/'

def index(request):
    return render(request, 'youtubeapp/index.html')

def index(request, page=0):
    max_page = YearMovie.objects.count() // 10
    return construct_page(request, MovieTagList.objects.values('content_id'), YearMovie.objects.order_by('-uptime_at')[page*10:(page+1)*10].values(), page, max_page, 'youtubeapp:index')

def construct_page(request, all_content_ids, page_contents, current_page, max_page, url_type, url_word=''):
    # page_contents(動画)に関連するタグを抜き出し、テンプレートで使えるよう整形
    contents = []
    for item in page_contents:
        tmp_dict = item
        tmp_dict.update({'tags': MovieTagList.objects.filter(content_id=item['id']).select_related('tag')})
        contents.append(tmp_dict)

    # all_content_idsからタグを多い順で集計し、整形する
    tag_cnt = MovieTagList.objects.filter(content__in = all_content_ids).values('tag').annotate(tag_count=Count('tag')).order_by('-tag_count')[:10]
    tag_names = [MovieTagName.objects.filter(id = item.get('tag'))[0] for item in tag_cnt]
    tags = [{'name': tag_names[i].name, 'count': tag_cnt[i]["tag_count"]} for i in range(len(tag_names))]

    # ページが有効な範囲をvalidでマークを付ける
    page_list = [{'num':x, 'valid':0 <= x and x <= max_page} for x in range(current_page-5, current_page+4)]

    return render(request, 'youtubeapp/index.html', {'tags': tags, 'contents': contents, 'page':{'type':url_type, 'word': url_word, 'current': current_page, 'max': max_page, 'list': page_list}})

def make_video_thumb(src_filename, capture_frame, dst_filename=None):
    probe = ffmpeg.probe(src_filename)
    video_info = next(x for x in probe['streams'] if x['codec_type'] == 'video')
    nframes = video_info['nb_frames']
    avg_frame_rate = (lambda x: int(x[0])/int(x[1])) (video_info['avg_frame_rate'].split('/'))
    start_position = int(capture_frame)/avg_frame_rate

    if dst_filename == None:
        out_target = 'pipe:'
    else:
        out_target = dst_filename

    im = (
        ffmpeg.input(src_filename, ss=start_position)
        .filter('scale', 200, -1)
        .output(out_target, vframes=1, format='image2', vcodec='mjpeg', loglevel='warning')
        .overwrite_output()
        .run(capture_stdout=True)
    )

    return im

def delete_video(content_id, video_filename):
    print('remove files at ' + str(content_id) + '/')
    storage = FileSystemStorage()
    storage.location = DATA_DIR
    storage.delete(str(content_id) + '/' + video_filename)
    storage.delete(str(content_id) + '/' + 'thumb.jpg')
    storage.delete(str(content_id) + '/')

def edit(request, content_id):
    content = get_object_or_404(YearMovie, pk=content_id)

    probe = ffmpeg.probe(DATA_DIR + str(content.id) + "/" + content.filename)
    video_info = next(x for x in probe['streams'] if x['codec_type'] == 'video')
    info = {'max_frame': video_info['nb_frames']}

    tags = MovieTagList.objects.filter(content_id=content_id).select_related('content')

    return render(request, 'video/edit.html', {'content':content, 'video_info':info, 'tags':tags})

def thumb(request, content_id, frame):
    content = get_object_or_404(YearMovie, pk=content_id)
    im = make_video_thumb(DATA_DIR + str(content.id) + "/" + content.movie_file, frame)
    return HttpResponse(im, content_type="image/jpeg")

def tag(request, tag_name, page=0):
    # tag_nameからIDを探し、見つかったIDを基にタグが付いた動画をフィルタする
    tag_id = MovieTagName.objects.filter(name=tag_name).get().id
    filtered_list = MovieTagList.objects.select_related('content').filter(tag=tag_id).order_by('-content__upload_date')

    max_page = filtered_list.count() // 10

    content_list = filtered_list[page*10:(page+1)*10]
    contents = [{'id':item.content.id, 'title':item.content.title} for item in content_list]

    return construct_page(request, filtered_list.values('content_id'), contents, page, max_page, 'video:tag', tag_name)

def search(request, search_word, page=0):
    filtered_list = YearMovie.objects.filter(title__contains=search_word).order_by('-upload_date')
    max_page = filtered_list.count() // 10
    content_list = filtered_list[page*10:(page+1)*10]
    contents = [{'id':item.id, 'title':item.title} for item in content_list]

    return construct_page(request, filtered_list.values('id'), contents, page, max_page, 'youtubeapp:search', search_word)

def search_post(request):
    if hasattr(request, 'POST') and 'search_text' in request.POST.keys():
        if request.POST['search_text'] != "":
            return HttpResponseRedirect(reverse('youtubeapp:search', args=(request.POST['search_text'],)))

    return HttpResponseRedirect(reverse('youtubeapp:index'))

def update(request, content_id):
    content = get_object_or_404(YearMovie, pk=content_id)
    content.title = request.POST['title']
    content.thumb_frame = request.POST['frame']
    content.description = request.POST['desc']
    content.save()

    make_video_thumb(DATA_DIR + str(content.id) + "/" + content.movie_file, content.thumb_frame, DATA_DIR + str(content.id) + "/thumb.jpg")

    return HttpResponseRedirect(reverse('video:index'))

def update_add_tag(request, content_id):
    if request.POST["tag"] != "":
        tag = MovieTagName.objects.filter(name=request.POST["tag"])
        if len(tag) == 0:
            tag = MovieTagName(name=request.POST["tag"])
            tag.save()
        else:
            tag = tag[0]

        tag_list = MovieTagList.objects.filter(tag_id=tag.id, content_id=content_id)
        if len(tag_list) == 0:
            tag_list = MovieTagList(tag_id=tag.id, content_id=content_id)
            tag_list.save()

    return HttpResponseRedirect(reverse('video:edit', kwargs={'content_id': content_id}))

def update_remove_tag(request, content_id, tag_name):
    tag = MovieTagName.objects.filter(name=tag_name)
    if len(tag) != 0:
        tag_list = MovieTagList.objects.filter(tag_id=tag[0].id, content_id=content_id)
        tag_list.delete()

    return HttpResponseRedirect(reverse('video:edit', kwargs={'content_id': content_id}))

class IndexView(ListView):
    template_name = 'index.html'
    queryset = YearMovie.objects.order_by('-uptime_at')
    paginate_by = 9

@method_decorator(login_required, name='dispatch')
class CreateMovieView(CreateView):
    form_class = YearMovieForm
    template_name = "post_movie.html"
    success_url = reverse_lazy('youtubeapp:post_done')
    def form_valid(self, form):
        upload_filename = form.cleaned_data["file"].name
        content = YearMovie(title=upload_filename, description="", uptime_at=timezone.now(), movie_file="")
        content.save()
        postdata = form.save(commit=False)
        postdata.user = self.request.user
        postdata.save()
        try:
            storage = FileSystemStorage()
            storage.location = DATA_DIR + str(content.id)
            filename = storage.save(upload_filename, form.cleaned_data["file"])
            make_video_thumb(DATA_DIR + str(content.id) + "/" + filename, content.thumb_frame, DATA_DIR + str(content.id) + "/thumb.jpg")
        except:
            delete_video(content.id, filename)
            content.delete()
            raise

        else:
            content.movie_file = filename
            content.save()

        return HttpResponseRedirect(reverse('youtubeapp:edit', args=(content.id,)))

class PostSuccessView(TemplateView):
    template_name ='post_success.html'

class VideoUploadForm(forms.Form):
    file = forms.FileField()

class MypageView(ListView):
    template_name = "mypage.html"
    paginate_by = 9
    def get_queryset(self):
        queryset = YearMovie.objects.filter(user=self.request.user).order_by(
            "-uptime_at"
        )

        return queryset

class CategoryView(ListView):
    template_name = "index.html"
    paginate_by = 9

    def get_queryset(self):
        category_id = self.kwargs["category"]
        categories = YearMovie.objects.filter(category=category_id).order_by(
            "-uptime_at"
        )
        return categories

class UserView(ListView):
    template_name = "index.html"
    paginate_by = 9

    def get_queryset(self):
        user_id = self.kwargs["user"]
        user_list = YearMovie.objects.filter(user=user_id).order_by("-uptime_at")
        return user_list

class DetailView(DetailView):
    template_name ='detail.html'
    model = YearMovie

class MovieDeleteView(DeleteView):
    template_name ='movie_delete.html'
    model = YearMovie
    success_url = reverse_lazy('youtubeapp:mypage')
    def delete(self, request, *args, **kwargs):
      return super().delete(request, *args, **kwargs)
      