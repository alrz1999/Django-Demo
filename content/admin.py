from django.contrib import admin

from content.models import Content, ContentScore, UpdateContentMeanScoreEvent


class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'score_sum', 'score_count', 'normalized_score_mean')
    readonly_fields = ('score_sum', 'score_count', 'normalized_score_mean')


class ContentScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'score', 'scored_at')
    readonly_fields = ('scored_at',)


class UpdateContentMeanScoreEventAdmin(admin.ModelAdmin):
    list_display = ('content', 'content_score', 'type', 'old_score', 'new_score', 'occurred_at')
    readonly_fields = ('occurred_at',)


# Register your models here.
admin.site.register(Content, ContentAdmin)
admin.site.register(ContentScore, ContentScoreAdmin)
admin.site.register(UpdateContentMeanScoreEvent, UpdateContentMeanScoreEventAdmin)
