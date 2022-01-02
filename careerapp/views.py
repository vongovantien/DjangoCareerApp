from typing import Union
from django.http import Http404
from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from django.db.models import F
from django.conf import settings
from rest_framework.decorators import permission_classes

from .models import Employer, Post, User, Category, Tag, Action, Rating, PostView, Comment, Recruitment, Candidate
from django.http import JsonResponse
from .serializers import (
    EmployerSerializer,
    PostSerializer,
    PostDetailSerializer,
    UserSerializer,
    CategorySerializer, ActionSerializer, PostViewSerializer, CommentSerializer, RatingSerializer, CandidateSerializer,
    EmployerDetailSerializer, RecruitmentSerializer
)
from .paginator import BasePagination
from rest_framework.generics import GenericAPIView
import random
import string

from twilio.rest import Client

ran_password = ''.join(random.choice(string.ascii_letters) for i in range(8))


# Tạo API lấy lại mật khẩu và gửi verify về điện thoại người dùng đăng ký lúc đầu
class ResetPassword(APIView):
    @permission_classes([permissions.IsAuthenticated])
    def post(self, request, *args, **kwargs):
        phone = request.data.get('phone')
        # username = request.data.get('username')
        # email = request.data.get('email')

        # Gán mật khẩu vào biến tạm
        temp = ran_password

        if phone:
            user = User.objects.filter(phone__iexact=phone).first()
            user.set_password(temp)
            user.save()

        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body="Mât khẩu khẩu mới của bạn là: " + str(temp),
            from_='+13074605629',
            to="+84" + phone[1:10]
        )

        if message:
            return Response({"success": "true"}, status=status.HTTP_200_OK)
        else:
            return Response({"success": "false"}, status=status.HTTP_404_NOT_FOUND)


# API cho phép thay đổi mật khẩu
class ChangePassword(APIView):
    @permission_classes([permissions.AllowAny])
    def post(self, request, *args, **kwargs):
        username = request.data['username']
        new_password = request.data['password']

        if username:
            user = User.objects.get(username=username)
            if new_password:
                user.set_password(new_password)
                user.save()

            return Response({"success": "true"}, status=status.HTTP_200_OK)

        return Response({"success": "false"}, status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, ]

    def get_permissions(self):
        if self.action == 'get_current_user':
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @action(methods=['get'], detail=False, url_path="current-user")
    def get_current_user(self, request):
        return Response(self.serializer_class(request.user, context={"request": request}).data,
                        status=status.HTTP_200_OK)


class AuthInfo(APIView):
    def get(self, request):
        return Response(settings.OAUTH2_INFO, status=status.HTTP_200_OK)


class EmployerPagination(PageNumberPagination):
    page_size = 10


class CommentPagination(PageNumberPagination):
    page_size = 5


class CategoryList(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        cate = Category.objects.all()
        category_id = self.request.query_params.get('category_id')

        if category_id is not None:
            cate = queryset.filter(post__category=category_id)

        return cate


# API comment
class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    pagination_class = CommentPagination
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        if request.user == self.get_object().creator:
            return super().destroy(request, *args, **kwargs)

        return Response(status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        if request.user == self.get_object().creator:
            return super().partial_update(request, *args, **kwargs)

        return Response(status=status.HTTP_403_FORBIDDEN)


# API trả về một ứng viên
class CandidateViewSet(viewsets.ViewSet, generics.RetrieveAPIView, generics.UpdateAPIView):
    serializer_class = CandidateSerializer
    queryset = Candidate.objects.all()


# API trả về một nhà tuyển dụng
class EmployerViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    serializer_class = EmployerDetailSerializer
    pagination_class = EmployerPagination

    def get_queryset(self):
        employer = Employer.objects.filter(active=True)

        kw = self.request.query_params.get('kw')
        cate = self.request.query_params.get('cate')

        if kw is not None:
            employer = employer.filter(name__icontains=kw)
        if cate is not None:
            employer = employer.filter(category_id__name__icontains=cate)

        return employer

    def get_permissions(self):
        if self.action in ['add_comment', 'rate']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['get'], detail=True, url_path='posts')
    def get_posts(self, request, pk):
        posts = Employer.objects.get(pk=pk).post.filter(active=True)

        return Response(PostSerializer(posts, many=True, context={"request": request}).data,
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="add-tags")
    def add_tags(self, request, pk):
        try:
            employer = self.get_object()
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            tags = request.data.get("tags")
            if tags is not None:
                for tag in tags:
                    t, _ = Tag.objects.get_or_create(name=tag)
                    employer.tags.add(t)

                employer.save()

                return Response(self.serializer_class(post).data,
                                status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], detail=True, url_path="comments")
    def get_comments(self, request, pk):
        p = self.get_object()
        return Response(
            CommentSerializer(p.comment_set.order_by("-id").all(), many=True,
                              context={"request": self.request}).data,
            status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='add-comment')
    def add_comment(self, request, pk):
        content = request.data.get('content')
        if content:
            c = Comment.objects.create(content=content, employer=self.get_object(), creator=request.user)
            return Response(CommentSerializer(c).data, status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, url_path="like")
    def take_action(self, request, pk):
        try:
            action_type = int(request.data['type'])
        except Union[IndexError, ValueError]:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            a = Action.objects.create(type=action_type, creator=request.user, employer=self.get_object())

            return Response(ActionSerializer(a).data,
                            status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="rating")
    def rate(self, request, pk):
        try:
            rating = int(request.data['rating'])
        except Union[IndexError, ValueError]:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            r = Rating.objects.update_or_create(creator=request.user,
                                                defaults={"rate": rating},
                                                employer=self.get_object())

            return Response(RatingSerializer(r).data,
                            status=status.HTTP_200_OK)


# API post
class PostViewSet(viewsets.ViewSet, generics.UpdateAPIView,
                  generics.RetrieveAPIView, generics.DestroyAPIView):
    serializer_class = PostDetailSerializer
    pagination_class = BasePagination
    queryset = Post.objects.filter(active=True)

    def get_queryset(self):
        posts = Post.objects.filter(active=True)

        q = self.request.query_params.get('q')
        cate = self.request.query_params.get('cate')
        city = self.request.query_params.get('city')

        if q is not None:
            posts = posts.filter(name__icontains=q)

        if cate is not None:
            if city == "":
                cate = None
                posts = posts.filter(category_id=cate)

        if city is not None:
            posts = posts.filter(location__icontains=city)

        return posts

    def get_permissions(self):
        if self.action in ['add_comment', 'talk_action', 'rate']:
            return [permissions.IsAuthenticated()]

        return [permissions.AllowAny()]

    @action(methods=['post'], detail=True, url_path="add-tags")
    def add_tags(self, request, pk):
        try:
            post = self.get_object()
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            tags = request.data.get("tags")
            if tags is not None:
                for tag in tags:
                    t, _ = Tag.objects.get_or_create(name=tag)
                    post.tags.add(t)

                post.save()

                return Response(self.serializer_class(post).data,
                                status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['post'], detail=True, url_path="recruitment")
    def recruitment(self, request, pk):
        Recruitment.objects.update_or_create(candidate=self.request.user, post=self.get_object())

        return Response({"Success": "true"}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="hide-post")
    def hide_post(self, request, pk):
        try:
            p = Post.objects.get(pk=pk)
            p.active = False
            p.save()
        except Post.DoesNotExits:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(data=PostSerializer(p, context={'request': request}).data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, url_path='views')
    def inc_view(self, request, pk):
        v, created = PostView.objects.get_or_create(post=self.get_object())
        v.views = F('views') + 1
        v.save()

        v.refresh_from_db()

        return Response(PostViewSerializer(v).data, status=status.HTTP_200_OK)
