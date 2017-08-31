# coding=gbk
from django.db import models

# Create your models here.
import datetime
from django.utils import timezone
from django.contrib.auth.models import User

class Question(models.Model):
    question_text = models.CharField( '问题内容', max_length = 120)
    pub_date = models.DateTimeField('出版日期')

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        #return self.pub_date >= timezone.now() - datetime.timedelta( days = 1)  # error sentence, used to test test
        now = timezone.now()
        return now - datetime.timedelta( days=10) <= self.pub_date <= now

    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'

    class Meta:
        permissions = (
            ('查看','查看问题'),
        )

class Choice(models.Model):
    question = models.ForeignKey( Question, on_delete = models.CASCADE )
    choice_text = models.CharField( 'choice text', max_length=80)
    votes = models.IntegerField( 'vote total', default=0 )

    def __str__(self):
        return self.choice_text

    class Meta:
        permissions = (
            ('view_Choice','View Choice'),
        )
    @models.permalink
    def get_absolute_url(self):
        return ('detail', (), {'question_id': self.question})

