from django.contrib.auth.models import User
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from .models import Content, ContentScore
from .serializers import ContentSerializer, ContentScoreSerializer

class UserMixin:
    def get_user(self):
        """
        Retrieves the user for the current request.
        If authenticated, uses request.user.
        If `user_id` is provided in the query params, fetches the user by ID.
        """
        if self.request.user.is_authenticated:
            return self.request.user

        user_id = self.request.query_params.get('user_id')
        if not user_id:
            user_id =  self.request.data.get('user_id')
        if user_id:
            user, created = User.objects.get_or_create(id=user_id, defaults={'username': f'user_{user_id}'})
            return user


        return None


class ContentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ContentListView(UserMixin, generics.ListAPIView):
    queryset = Content.objects.order_by('id').all()
    serializer_class = ContentSerializer
    pagination_class = ContentPagination

    def paginate_queryset(self, queryset, *args, **kwargs):
        paginated_data = super().paginate_queryset(queryset)
        if paginated_data is None:
            return None

        return self.attach_current_user_score(paginated_data)

    def attach_current_user_score(self, paginated_data):
        """
        Fetches the related ContentScore for the given user and attaches the score to each content.
        """
        user = self.get_user()

        if user:
            content_ids = [content.id for content in paginated_data]
            content_scores = ContentScore.objects.filter(
                user=user, content_id__in=content_ids
            ).select_related('content')

            content_scores_by_content_id = {score.content_id: score for score in content_scores}
            for content in paginated_data:
                content.user_score = content_scores_by_content_id.get(content.id)

        return paginated_data


class ContentScoreCreateUpdateView(UserMixin, generics.CreateAPIView):
    queryset = ContentScore.objects.all()
    serializer_class = ContentScoreSerializer

    def perform_create(self, serializer):
        user = self.get_user()
        if user is None:
            raise serializers.ValidationError({"user": "user_id is required."})

        serializer.save(user=user)