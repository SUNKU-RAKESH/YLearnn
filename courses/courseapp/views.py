from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg
from django.http import HttpResponse
from reportlab.pdfgen import canvas

from .models import Course, Enrollment, Video, Profile, CourseReview, CourseProgress

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user, role=role)
        return redirect('login')
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('course_list')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

'''@login_required
def course_list(request):
    courses = Course.objects.all().annotate(avg_rating=Avg('reviews__rating'))
    sort_option = request.GET.get('sort')
    if sort_option == 'rating':
        courses = courses.order_by('-avg_rating')
    elif sort_option == 'default':
        courses = courses.order_by('-created_at')
    return render(request, 'course_list.html', {'courses': courses}) '''
from django.db.models import Q
@login_required
def course_list(request):
    search_query = request.GET.get('search', '')
    sort_option = request.GET.get('sort')

    courses = Course.objects.all()

    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    courses = courses.annotate(avg_rating=Avg('reviews__rating'))

    if sort_option == 'rating':
        courses = courses.order_by('-avg_rating')
    elif sort_option == 'default':
        courses = courses.order_by('-created_at')

    return render(request, 'course_list.html', {'courses': courses, 'search_query': search_query})



@login_required
def enroll_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    Enrollment.objects.get_or_create(student=request.user, course=course)
    return redirect('course_detail', pk=pk)

@login_required
def create_course(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'tutor':
        return redirect('course_list')
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        thumbnail = request.FILES.get('thumbnail')
        price = request.POST.get('price', '0').strip()
        try:
            price = float(price)
        except ValueError:
            price = 0.00
        Course.objects.create(
            title=title,
            description=description,
            instructor=request.user,
            thumbnail=thumbnail,
            price=price
        )
        return redirect('course_list')
    return render(request, 'create_course.html')

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    profile = get_object_or_404(Profile, user=request.user)
    is_tutor = profile.role == 'tutor'
    enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    reviews = course.reviews.all()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    videos = course.videos.all()
    total_videos = videos.count()
    watched_videos = CourseProgress.objects.filter(user=request.user, course=course, watched=True).values_list('video_id', flat=True)
    completed_videos = len(watched_videos)
    percentage = int((completed_videos / total_videos) * 100) if total_videos else 0

    if request.method == 'POST':
        if is_tutor and request.FILES.get('video_file'):
            title = request.POST.get('title')
            video_file = request.FILES.get('video_file')
            thumbnail = request.FILES.get('thumbnail')
            Video.objects.create(course=course, title=title, video_file=video_file, thumbnail=thumbnail)
            return redirect('course_detail', pk=pk)
        if not is_tutor and enrolled and request.POST.get('rating'):
            rating = int(request.POST.get('rating'))
            feedback = request.POST.get('feedback', '')
            CourseReview.objects.update_or_create(
                course=course, student=request.user,
                defaults={'rating': rating, 'feedback': feedback}
            )
            return redirect('course_detail', pk=pk)

    return render(request, 'course_detail.html', {
        'course': course,
        'enrolled': enrolled,
        'is_tutor': is_tutor,
        'reviews': reviews,
        'average_rating': round(average_rating, 1),
        'videos': videos,
        'watched_videos': watched_videos,
        'percentage': percentage
    })

@login_required
def mark_video_watched(request, course_id, video_id):
    course = get_object_or_404(Course, id=course_id)
    video = get_object_or_404(Video, id=video_id, course=course)
    CourseProgress.objects.get_or_create(user=request.user, course=course, video=video, defaults={'watched': True})
    return redirect('course_detail', pk=course.id)
'''
@login_required
def download_certificate(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    total_videos = course.videos.count()
    watched_count = CourseProgress.objects.filter(user=request.user, course=course, watched=True).count()

    if total_videos == 0 or watched_count < total_videos:
        return render(request, 'certificate_error.html', {'message': 'Please complete all videos to download certificate.'})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{course.title}_certificate.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(150, 750, "Certificate of Completion")
    p.setFont("Helvetica", 16)
    p.drawString(100, 700, f"This certifies that {request.user.username}")
    p.drawString(100, 675, f"has successfully completed the course:")
    p.setFont("Helvetica-Bold", 18)
    p.drawString(100, 650, f"{course.title}")
    p.setFont("Helvetica", 14)
    p.drawString(100, 600, "Date of Issue: " + timezone.now().strftime('%B %d, %Y'))
    p.showPage()
    p.save()
    return response
'''
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Course

from reportlab.pdfgen import canvas
from io import BytesIO

@login_required
def download_certificate(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    student = request.user

    # Create a byte stream buffer
    buffer = BytesIO()

    # Create a PDF canvas
    p = canvas.Canvas(buffer)

    # Add content to the PDF
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "Certificate of Completion")

    p.setFont("Helvetica", 14)
    p.drawString(100, 700, f"This is to certify that {student.get_full_name() or student.username}")
    p.drawString(100, 675, f"has successfully completed the course:")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 650, f"{course.title}")

    p.setFont("Helvetica", 12)
    p.drawString(100, 600, f"Date: {course.created_at.strftime('%B %d, %Y')}")
    p.drawString(100, 580, "Congratulations and best wishes!")

    # Finalize PDF
    p.showPage()
    p.save()

    # Move buffer to beginning
    buffer.seek(0)

    # Return as response
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{course.title}_certificate.pdf"'
    return response


@login_required
def dashboard_redirect(request):
    profile = request.user.profile
    if profile.role == 'student':
        return redirect('student_dashboard')
    elif profile.role == 'tutor':
        return redirect('tutor_dashboard')
    return redirect('home')  # default fallback


@login_required
def student_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'student':
        return redirect('course_list')

    # access using the related_name you just defined
    enrollments = request.user.enrollments.select_related('course')
    return render(request, 'student_dashboard.html', {'enrollments': enrollments})


@login_required
def tutor_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.role != 'tutor':
        return redirect('course_list')

    my_courses = Course.objects.filter(instructor=request.user)
    return render(request, 'tutor_dashboard.html', {'courses': my_courses})

