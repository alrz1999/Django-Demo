from django.test import TestCase
from .models import Content, ContentScore
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ContentNormalizationTests(TestCase):
    def setUp(self):
        # Create sample users
        self.user1 = User.objects.create(username='user1', id=1)
        self.user2 = User.objects.create(username='user2', id=2)
        self.user3 = User.objects.create(username='user3', id=3)
        self.user4 = User.objects.create(username='user4', id=4)

        # Create a content instance
        self.content = Content.objects.create(title='Sample Content', text='This is a sample content.')

        # Create sample scores for the content
        self.create_sample_scores()

    def create_sample_scores(self):
        # Create ContentScore instances
        now = timezone.now()

        # Normal scores (between 0 and 5)
        ContentScore.objects.create(content=self.content, user=self.user1, score=3, scored_at=now)
        ContentScore.objects.create(content=self.content, user=self.user2, score=4, scored_at=now - timedelta(hours=1))
        ContentScore.objects.create(content=self.content, user=self.user3, score=5, scored_at=now - timedelta(hours=2))

        # Outlier score (should be excluded in normalization, but still in range for testing)
        ContentScore.objects.create(content=self.content, user=self.user4, score=0, scored_at=now - timedelta(hours=3))  # Changed to 0 to fit the valid range

        self.content.refresh_from_db()

    def test_calculate_normalized_score_mean(self):
        # Calculate the normalized score mean
        normalized_mean = self.content.calculate_normalized_score_mean(1.5)

        # Check that the outlier (0) is correctly handled, should still exclude it if you have filtering logic
        expected_mean = (3 + 4 + 5) / 3  # Excluding the outlier score of 0 in this case
        self.assertAlmostEqual(normalized_mean, expected_mean, places=2)

    def test_calculate_score_mean(self):
        # Calculate the average score mean without filtering
        score_mean = self.content.calculate_score_mean()

        # The mean should consider all scores including the score of 0
        expected_mean_with_outlier = (3 + 4 + 5 + 0) / 4  # Including the score of 0
        self.assertAlmostEqual(score_mean, expected_mean_with_outlier, places=2)
