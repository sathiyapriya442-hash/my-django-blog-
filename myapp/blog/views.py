from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User  # Import User model
from django.contrib.auth.models import Group

import logging

from .models import Category, Post, AboutUs
from .forms import ContactForm, LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm, PostForm

# Home page view
def index(request):
    blog_title = "Latest posts"
    all_posts = Post.objects.filter(is_published=True)
    paginator = Paginator(all_posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/index.html', {'blog_title': blog_title, 'page_obj': page_obj})

# Post detail view
def detail(request, slug):
    if request.user and not request.user.has_perm('blog_view_post'):
        messages.error(request, 'You have no permisson to view any posts')
        return redirect('blog:index')
    try:
        post = Post.objects.get(slug=slug, is_published=True)
        related_posts = Post.objects.filter(category=post.category).exclude(pk=post.id)[:3]
    except Post.DoesNotExist:
        raise Http404("Post does not exist!")
    return render(request, 'blog/detail.html', {'post': post, 'related_posts': related_posts})

# Old to new URL redirect
def old_url_redirect(request):
    return redirect(reverse('blog:new_page_url'))

def new_url_view(request):
    return HttpResponse("This is the new URL")

# Custom 404 page
def custom_page_not_found(request, exception):
    return render(request, '404.html', status=404)

# Contact form view
def contact(request):
    logger = logging.getLogger("TESTING")
    success_message = ''
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            logger.debug(f"POST data is {name} {email} {message}")
            success_message = 'Your email has been sent!'
            form = ContactForm()
            return render(request, 'blog/contact.html', {'form': form, 'success_message': success_message})
        else:
            logger.debug('Form validation failure')
            logger.debug(form.errors)
            return render(request, 'blog/contact.html', {'form': form})
    
    form = ContactForm()
    return render(request, 'blog/contact.html', {'form': form})

# About page view
def about(request):
    about_content = AboutUs.objects.first()
    if about_content is None or not about_content.content:
        about_content = "Default content goes here."
    else:
        about_content = about_content.content
    return render(request, 'blog/about.html', {'about_content': about_content})

# Register view
def register(request):
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            #add user to readers group
            readers_group,created = Group.objects.get_or_create(name="Readers")
            user.groups.add(readers_group)
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect("blog:login")
    return render(request, 'blog/register.html', {'form': form})

# Login view
def login(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect("blog:dashboard")
            messages.error(request, "Invalid username or password.")
    return render(request, 'blog/login.html', {'form': form})

# Dashboard view
@login_required
@permission_required('blog.add_post', raise_exception=True)
def dashboard(request):
    blog_title = "My Posts"
    all_posts = Post.objects.filter(user=request.user)
    paginator = Paginator(all_posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/dashboard.html', {"blog_title": blog_title, 'page_obj': page_obj})

# Logout view
def logout(request):
    auth_logout(request)
    return redirect("blog:index")

# Forgot password view
def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                current_site = get_current_site(request)
                domain = current_site.domain
                subject = "Reset Password Request"
                message = render_to_string('blog/reset_password_email.html', {
                    'domain': domain,
                    'uid': uid,
                    'token': token,
                    'user': user,
                })

                send_mail(subject, message, 'noreply@priya.com', [email])
                messages.success(request, 'Reset password email has been sent.')
            except User.DoesNotExist:
                messages.error(request, 'No user found with that email.')

    return render(request, 'blog/forgot_password.html', {'form': form})

# Reset password view
def reset_password(request, uidb64=None, token=None):
    form = ResetPasswordForm()
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            try:
                uid = urlsafe_base64_decode(uidb64)
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password reset successfully. You can now log in.")
                return redirect("blog:login")
            else:
                messages.error(request, "The reset link is invalid or has expired.")

    return render(request, 'blog/reset_password.html', {'form': form})

# New post view
@login_required
def new_post(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('blog:dashboard')
    else:
        form = PostForm()

    return render(request, 'blog/new_post.html', {'categories': categories, 'form': form})

# Edit post view
@login_required
def edit_post(request, post_id):
    categories = Category.objects.all()
    post = get_object_or_404(Post, id=post_id)
    
    if post.user != request.user:
        messages.error(request, "You are not authorized to edit this post.")
        return redirect('blog:dashboard')

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully!")
            return redirect('blog:dashboard')
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/edit_post.html', {'categories': categories, 'post': post, 'form': form})

# ✅ Delete post view
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    messages.success(request, "Post deleted successfully!")
    return redirect('blog:dashboard')
@login_required
def publish_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_published = True
    post.save()
    messages.success(request, "Post published successfully!")
    return redirect('blog:dashboard')
    

    