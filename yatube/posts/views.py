from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow

COUNT_OF_POSTS_DEFAULT = 10


def get_page_obj(posts: list,
                 page_number: int,
                 paginator_count_of_posts: int = COUNT_OF_POSTS_DEFAULT
                 ) -> int:
    paginator = Paginator(posts, paginator_count_of_posts)
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request: HttpRequest) -> HttpResponse:
    template = 'posts/index.html'

    posts = Post.objects.select_related('author', 'group')
    page_number = request.GET.get('page')
    page_obj = get_page_obj(posts, page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request: HttpRequest, slug) -> HttpResponse:
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_number = request.GET.get('page')
    page_obj = get_page_obj(posts, page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request: HttpRequest, username) -> HttpResponse:
    tempalate = 'posts/profile.html'

    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    page_number = request.GET.get('page')
    page_obj = get_page_obj(posts, page_number)

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=author)

    context = {
        'following': following,
        'page_obj': page_obj,
        'author': author,
    }
    return render(request, tempalate, context)


def post_detail(request: HttpRequest, post_id) -> HttpResponse:
    tempalate = 'posts/post_detail.html'

    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'author': author,
        'comments': comments,
        'form': form,
    }
    return render(request, tempalate, context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            form.instance.author = request.user
            form.save()
            return redirect('posts:profile', username=request.user.username)

    form = PostForm()

    context = {
        'form': form
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'

    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)

    form = PostForm(
        request.POST or None,
        instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow_author_posts = Post.objects.select_related('author').filter(
        author__following__user=request.user)
    page_number = request.GET.get('page')
    page_obj = get_page_obj(follow_author_posts, page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', request.user)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', request.user)
