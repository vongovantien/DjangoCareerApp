from datetime import datetime

from django.contrib import admin
from django.contrib.auth.models import Permission
from django import forms
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.template.response import TemplateResponse
from django.utils.html import mark_safe
from .models import Employer, Tag, Category, Post, User, EmployerImage, Recruitment, Candidate
from django.urls import path
from django.utils.html import format_html


class EmployerTagInline(admin.TabularInline):
    model = Employer.tags.through
    extra = 1


class PostInline(admin.StackedInline):
    model = Post
    pk_name = "employers"
    extra = 1


class EmployerImageInline(admin.TabularInline):
    model = EmployerImage
    readonly_fields = ["image_tag"]
    extra = 3


class EmployerAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ['/static/css/main.css', ]
        }

    inlines = (PostInline, EmployerTagInline, EmployerImageInline)
    list_display = ["id", "name", "location", "created_date", "active"]
    search_fields = ["name", "created_date", "location"]
    list_filter = ["name", "created_date", "location"]
    readonly_fields = ["logo_company"]

    def logo_company(self, employer):
        return mark_safe("<img src='/media/{img_url}' alt='{alt}' width='120px'/>".
                         format(img_url=employer.logo.name, alt=employer.name))


class JobAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "salary", "skill", "quantity", "location", "created_date"]
    search_fields = ["name", "created_date", "salary", "skill"]
    list_filter = ["name", "created_date", "salary", "skill"]


class PostAdmin(admin.ModelAdmin):
    title = 'Productive author'

    @admin.display(description='Ngày tuyển dụng')
    def hide_date(self, obj):
        return obj.hide_begin.strftime('%d-%m-%Y')

    @admin.display(description='Ngày kết thúc')
    def end_date(self, obj):
        return obj.hide_end.strftime('%d-%m-%Y')

    @admin.display(description='Vị trí')
    def upper_case_location(self, obj):
        return ("%s" % obj.location).upper()

    @admin.display(description="Tên công việc")
    def colored_name(self, obj):
        return format_html(
            '<span style="color: green;">{}<span>',
            obj.name,
        )

    list_display = ["colored_name", "upper_case_location", "category", "hide_date", "end_date"]
    search_fields = ["employers", "created_date", "name", "location"]
    list_filter = ["employers", "name", "location", "category"]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


class CandidateAdmin(admin.ModelAdmin):
    list_display = ["name", "address", "birthday", "active"]
    search_fields = ["name"]
    list_filter = ["name"]


class TagAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


class CareerAppAdminSite(admin.AdminSite):
    site_header = "HỆ THỐNG QUẢN LÍ TRANG TUYỂN DỤNG"
    site_title = "Admin"
    index_title = "CareerApp"

    def get_urls(self):
        return [
                   path('post-cate/', self.post_cate),
                   path('post-year/', self.post_year),
                   path('post-date/', self.post_date),
                   path('cate-by-year/', self.cate_by_year),
               ] + super().get_urls()

    def post_cate(self, request):
        kw = request.POST.get('kw')

        post_count = Post.objects.filter(active=True).count()
        post_category = Category.objects

        if kw is not None:
            post_category = post_category.filter(name__icontains=kw)

        post_category = post_category.annotate(posts=Count('post')) \
            .values("id", "name", "posts") \
            .order_by("-posts", "id")

        return TemplateResponse(request, 'admin/post-cate.html', {
            'post_count': post_count,
            'post_category': post_category,
        })

    def post_year(self, request):
        year = request.POST.get('year')

        if year.__eq__(""):
            year = datetime.now().year

        post_cate = Category.objects.all()

        if year is not None:
            post_cate = post_cate.filter(post__created_date__year=year) \
                .annotate(month=ExtractMonth('post__created_date')) \
                .values('month') \
                .annotate(posts=Count('post')) \
                .values('month', 'posts') \
                .order_by('month')

        return TemplateResponse(request, 'admin/post-year.html', {
            'post_cate': post_cate
        })

    def cate_by_year(self, request):
        year = request.POST.get('year')

        if year.__eq__(""):
            year = datetime.now().year

        c = Category.objects.all()

        if year is not None:
            c = c.filter(post__created_date__year=year) \
                .annotate(posts=Count('post')) \
                .values('id', 'name', 'posts') \
                .order_by('name')

        return TemplateResponse(request, 'admin/cate-by-year.html', {
            'cate_by_year': c
        })

    def post_date(self, request):
        from_date = request.POST.get('fromDate', None)
        to_date = request.POST.get('toDate', None)

        if from_date == "":
            from_date = None
        if to_date == "":
            to_date = None

        post_date = Category.objects

        if from_date is not None:
            post_date = post_date.filter(post__created_date__gte=datetime.strptime(from_date, '%Y-%m-%d'))
        if to_date is not None:
            post_date = post_date.filter(post__created_date__lte=datetime.strptime(to_date, '%Y-%m-%d'))

        post_date = post_date.annotate(posts=Count('post')).values("id", "name", "posts")

        return TemplateResponse(request, 'admin/post-date.html', {
            'post_date': post_date,
        })


admin_site = CareerAppAdminSite(name="CareerApp")

admin_site.register(Post, PostAdmin)
admin_site.register(Employer, EmployerAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(User),
admin_site.register(Permission),
admin_site.register(Candidate, CandidateAdmin),

admin.site.register(Employer, EmployerAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(User),
admin.site.register(Permission),
admin.site.register(Candidate, CandidateAdmin),
