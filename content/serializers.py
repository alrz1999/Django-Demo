from django.utils import timezone
from rest_framework import serializers

from content.models import Content, ContentScore


class ContentSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()
    user_score = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = ['id', 'title', 'score', 'score_count', 'user_score']

    @staticmethod
    def get_score(obj):
        return obj.get_score()

    @staticmethod
    def get_user_score(obj):
        if hasattr(obj, 'user_score') and obj.user_score:
            return obj.user_score.score
        return None


class ContentScoreSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(required=True)

    class Meta:
        model = ContentScore
        fields = ['content', 'score']

    def create(self, validated_data):
        user = validated_data['user']
        content = validated_data['content']
        new_score = validated_data['score']
        scored_at = timezone.now()

        content_score, created = ContentScore.objects.update_or_create(
            user=user, content=content,
            defaults={
                'score': new_score,
                'scored_at': scored_at
            }
        )

        return content_score
