from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group,
         'posts': posts,
         'page': page,
         'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    count = author.posts.count()
    return render(request, 'profile.html',
                  {'page': page,
                   'author': author,
                   'paginator': paginator,
                   'count': count})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    count = author.posts.count()
    form = CommentForm()
    items = post.comments.all()
    return render(request,
                  'post.html',
                  {'post': post,
                   'count': count,
                   'author': author,
                   'form': form,
                   'items': items})


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username, post_id=post_id)

    return render(
        request, 'new_post.html', {'form': form, 'post': post},
    )


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username,
                             id=post_id)
    items = post.comments.all()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.post = post
        new_comment.author = request.user
        new_comment.save()
        return redirect('post', username=post.author,
                        post_id=post.id)
    return render(request, 'post.html', {
        'form': form,
        'items': items,
        'post_profile': post,
        'user_profile': post.author})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__in=Follow.objects.filter(user=request.user))
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    user = User.objects.get(username=request.user)
    author = User.objects.get(username=username)
    follower = Follow.objects.create(user=user, author=author)
    follower.save()
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    # follower = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    un_follow = Follow.objects.get(user=request.user, author=author)
    un_follow.delete()
    # if follower.follower.filter(author=author).exists() and follower != author:
    #     follower.follower.get(author=author).delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
