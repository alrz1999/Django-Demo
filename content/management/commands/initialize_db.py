from django.core.management.base import BaseCommand
from content.models import Content, ContentScore
from django.contrib.auth.models import User
import random
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Initialize the database with sample contents and scores for testing normalization'

    def handle(self, *args, **kwargs):
        # Create a large number of sample users
        users = [User.objects.get_or_create(username=f'user{i}')[0] for i in range(1, 101)]  # 100 users

        # Create sample contents
        contents = [

            Content.objects.get_or_create(title=f'Content {i}', text=f'This is the content text for item {i}.')[0]
            for i in range(1, 6)
        ]

        # Generate scores for each content
        for content in contents:
            # Simulate normal scores from the first 80 users
            for user in users[:80]:  # First 80 users give normal scores
                score = random.randint(3, 5)  # Normal scores between 3 and 5
                scored_at = timezone.now() - timedelta(hours=random.randint(0, 19))  # Random time within the first 20 hours
                ContentScore.objects.create(user=user, content=content, score=score, scored_at=scored_at)

            # Simulate a surge of low scores from the last 20 users
            for user in users[80:]:  # Last 20 users give low scores
                score = random.randint(0, 1)  # Low scores (0 or 1)
                scored_at = timezone.now() - timedelta(hours=random.randint(20, 23))  # Random time within the last 4 hours
                ContentScore.objects.create(user=user, content=content, score=score, scored_at=scored_at)

        self.stdout.write(self.style.SUCCESS('Successfully initialized the database with sample data.'))
