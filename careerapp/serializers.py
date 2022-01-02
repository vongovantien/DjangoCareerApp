import json
import random

from rest_framework import serializers
from django.contrib.admin.templatetags.admin_list import pagination
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, HyperlinkedModelSerializer, Serializer
from .models import Employer, Post, Tag, User, Category, Action, Rating, PostView, Comment, EmployerImage, Recruitment, \
    Candidate


# Tạo user
class UserSerializer(ModelSerializer):
    avatar = SerializerMethodField()

    def get_avatar(self, user):
        request = self.context['request']
        if user.avatar:
            name = user.avatar.name
            if name.startswith("media/"):
                path = '/%s' % name
            else:
                path = '/media/%s' % name

            return request.build_absolute_uri(path)

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(user.password)
        user.save()

        return user

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "username",
                  "password", "avatar", "date_joined"]
        extra_kwargs = {
            'password': {'write_only': 'true'}
        }


# Trả về danh mục ngành
class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


# Trả về comment
class CommentSerializer(ModelSerializer):
    creator = SerializerMethodField()

    def get_creator(self, comment):
        return UserSerializer(comment.creator, context={"request": self.context.get('request')}).data

    class Meta:
        model = Comment
        fields = "__all__"


# Trả về cho phép ứng viên nộp hồ sơ
class RecruitmentSerializer(ModelSerializer):
    class Meta:
        model = Recruitment
        fields = "__all__"


# Trả về tag
class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class EmployerImageSerializer(ModelSerializer):
    class Meta:
        model = EmployerImage
        fields = "__all__"

    def get_image(self, employerimage):
        request = self.context['request']
        name = employerimage.image.name
        if name.startswith("media/"):
            path = '/%s' % name
        else:
            path = '/media/%s' % name

        return request.build_absolute_uri(path)


# Hiển thị thông tin ứng viên
class CandidateSerializer(ModelSerializer):
    # user = UserSerializer()

    class Meta:
        model = Candidate
        fields = "__all__"


# Hiển thị nhà tuyển dụng
class EmployerSerializer(ModelSerializer):
    logo = SerializerMethodField()
    category = CategorySerializer()

    def get_logo(self, employer):
        request = self.context['request']
        name = employer.logo.name
        if name.startswith("media/"):
            path = '/%s' % name
        else:
            path = '/media/%s' % name

        return request.build_absolute_uri(path)

    def get_category(self, post):
        return CategorySerializer(post.category, context={"request": self.context.get('request')}).data

    class Meta:
        model = Employer
        fields = ["id", "name", "logo", "location", "category", "contact_name", "contact_email", "address"]


# Trả ra chi tiết của một nhà tuyển dụng
class EmployerDetailSerializer(EmployerSerializer):
    tags = TagSerializer(many=True)
    category = SerializerMethodField()
    images = EmployerImageSerializer(many=True)
    rate = SerializerMethodField()

    def get_rate(self, employer):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            r = employer.rating_set.filter(creator=request.user).first()
            if r:
                return r.rate

        return -1

    class Meta:
        model = EmployerSerializer.Meta.model
        fields = EmployerSerializer.Meta.fields + ["images", "address", "created_date", "tags", "info_employer", "rate"]


# Hiển thị bài đăng
class PostSerializer(ModelSerializer):
    employers = SerializerMethodField()

    def get_employers(self, post):
        return EmployerSerializer(post.employers, context={"request": self.context.get('request')}).data

    class Meta:
        model = Post
        fields = ["id", "name", "created_date", "location", "salary", "employers", "category"]


# Hiển thị chi tiết một bài đăng
class PostDetailSerializer(PostSerializer):
    tags = TagSerializer(many=True)
    category = SerializerMethodField()
    employers = SerializerMethodField()

    def get_category(self, post):
        return CategorySerializer(post.category, context={"request": self.context.get('request')}).data

    def get_employers(self, post):
        return EmployerSerializer(post.employers, context={"request": self.context.get('request')}).data

    class Meta:
        model = Post
        fields = PostSerializer.Meta.fields + ["description", "benefit", "requirement", "tags", "experience",
                                               "category", "quantity", "hide_begin",
                                               "hide_end", "position"]


# Đánh giá một nhà tuyển dụng
class RatingSerializer(ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'rate', 'created_date']


# Xem lượt view của một bài tuyển dụng
class PostViewSerializer(ModelSerializer):
    class Meta:
        model = PostView
        exclude = ['created_date', 'updated_date']


class ActionSerializer(ModelSerializer):
    class Meta:
        model = Action
        fields = ['id', 'type', 'created_date']
