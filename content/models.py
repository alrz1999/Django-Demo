import logging
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.models import Avg, F, Count, ExpressionWrapper, FloatField, Q
from django.db.models.functions import TruncHour, Abs
from rest_framework.exceptions import ValidationError

from content.utils import filter_outliers

logger = logging.getLogger(__name__)


class Content(models.Model):
    NORMALIZED_MEAN_MAXIMUM_DIFFERENCE = 1

    title = models.CharField(max_length=255)
    text = models.TextField()

    score_count = models.IntegerField(default=0)
    score_sum = models.IntegerField(default=0)
    normalized_score_mean = models.FloatField(null=True, blank=True)

    def get_score(self):
        exact_mean = self.calculate_score_mean()
        if exact_mean is None:
            return None

        if self.normalized_score_mean is None:
            return exact_mean

        if abs(self.normalized_score_mean - exact_mean) < Content.NORMALIZED_MEAN_MAXIMUM_DIFFERENCE:
            return exact_mean
        else:
            return self.normalized_score_mean

    def calculate_score_mean(self):
        if self.score_count > 0:
            return self.score_sum / self.score_count
        return None

    def calculate_normalized_score_mean(self, z_threshold=2.0):
        hourly_data = (
            ContentScore.objects.filter(content=self)
            .annotate(hour=TruncHour('scored_at'))
            .values('hour')
            .annotate(score_count=Count('id'), score_mean=Avg('score'))
            .order_by('hour')
        )

        filtered_data = filter_outliers(hourly_data, z_threshold)
        total_count = sum([h['score_count'] for h in filtered_data])
        if total_count == 0:
            return self.calculate_score_mean()

        weighted_sum = sum([h['score_mean'] * h['score_count'] for h in filtered_data])
        return weighted_sum / total_count

    def update_normalized_score_mean(self):
        try:
            logger.info(f"Starting normalization score update for Content ID {self.id} - Title: {self.title}")
            new_mean = self.calculate_normalized_score_mean()
            logger.info(f"Calculated normalized score mean: {new_mean} for Content ID {self.id}")
            self.normalized_score_mean = new_mean
            self.save(update_fields=['normalized_score_mean'])
            logger.info(f"Successfully updated normalized score mean for Content ID {self.id}")
        except Exception as e:
            logger.error(f"Error updating normalized score mean for Content ID {self.id}: {str(e)}", exc_info=True)

    @classmethod
    def get_candidates_for_normalization(cls, threshold):
        score_mean_expr = ExpressionWrapper(
            F('score_sum') / F('score_count'),
            output_field=FloatField()
        )

        return Content.objects.annotate(
            score_mean=score_mean_expr,
            abs_difference=Abs(score_mean_expr - F('normalized_score_mean'))
        ).filter(
            Q(normalized_score_mean__isnull=True) |
            Q(abs_difference__gt=threshold)
        )

    def __str__(self):
        return f"{self.title}"


class ContentScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    scored_at = models.DateTimeField()

    class Meta:
        unique_together = (('user', 'content'),)

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.validate_score()
        try:
            with transaction.atomic():
                logger.debug(
                    f"Transaction started for saving ContentScore (User ID: {self.user.id}, Content ID: {self.content.id}).")

                old_content_score = ContentScore.objects.filter(user=self.user,
                                                                content=self.content).select_for_update().first()
                super().save(force_insert, force_update, using, update_fields)
                logger.info(
                    f"ContentScore saved for User ID {self.user.id}, Content ID {self.content.id}, Score: {self.score}.")
                if old_content_score is None:
                    UpdateContentMeanScoreEvent.objects.create(
                        content=self.content,
                        content_score=self,
                        type=UpdateContentMeanScoreEvent.Type.ADD_SCORE,
                        old_score=None,
                        new_score=self.score,
                    )
                    logger.info(f"ADD_SCORE event created for Content ID {self.content.id} with score {self.score}.")
                elif old_content_score.score != self.score:
                    UpdateContentMeanScoreEvent.objects.create(
                        content=self.content,
                        content_score=self,
                        type=UpdateContentMeanScoreEvent.Type.UPDATE_SCORE,
                        old_score=old_content_score.score,
                        new_score=self.score,
                    )
                    logger.info(
                        f"UPDATE_SCORE event created for Content ID {self.content.id}. Old score: {old_content_score.score}, New score: {self.score}.")
        except Exception as e:
            logger.error(
                f"Error occurred while saving ContentScore for User ID {self.user.id}, Content ID {self.content.id}: {str(e)}",
                exc_info=True)
            raise

    def validate_score(self):
        if self.score < 0 or self.score > 5:
            raise ValidationError('Score must be between 0 and 5.')

    def __str__(self):
        return f"{self.user} -> {self.content}: {self.score}"


class UpdateContentMeanScoreEvent(models.Model):
    class Type(models.TextChoices):
        ADD_SCORE = 'ADD_SCORE', 'Add score'
        UPDATE_SCORE = 'UPDATE_SCORE', 'Update score'

    content = models.ForeignKey(Content, on_delete=models.CASCADE)
    content_score = models.ForeignKey(ContentScore, on_delete=models.CASCADE)
    type = models.CharField(choices=Type.choices, default=Type.ADD_SCORE, max_length=20)
    old_score = models.IntegerField(null=True, blank=True)
    new_score = models.IntegerField()
    occurred_at = models.DateTimeField(auto_now_add=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            with transaction.atomic():
                super().save(force_insert, force_update, using, update_fields)
                if self.type == UpdateContentMeanScoreEvent.Type.ADD_SCORE:
                    Content.objects.filter(id=self.content.id).update(
                        score_sum=F('score_sum') + self.get_score_change(),
                        score_count=F('score_count') + 1,
                    )
                elif self.type == UpdateContentMeanScoreEvent.Type.UPDATE_SCORE:
                    Content.objects.filter(id=self.content.id).update(
                        score_sum=F('score_sum') + self.get_score_change(),
                    )
                else:
                    raise Exception("type {} is not valid".format(self.type))
        except Exception as e:
            logger.error(f"Error occurred during save for content {self.content.id}: {str(e)}", exc_info=True)
            raise

    def get_score_change(self):
        if self.old_score:
            return self.new_score - self.old_score
        return self.new_score

    def __str__(self):
        return f"{self.type} -> {self.old_score} -> {self.new_score}"
