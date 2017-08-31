#coding=gbk
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from django.utils import timezone

from django.contrib.auth.models import User

from guardian.decorators import permission_required_or_403

from .models import Choice, Question

# Create your views here.

class IndexView( generic.ListView ):
    #boss = User.objects.create(username='Joe')
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    
    def get_queryset(self):
        """
        Return the last five published questions. ( not including those set to
        be published in the future).  lte =  less than or equal to
        
        """
        s = Question.objects.filter(
                pub_date__lte=timezone.now() # pub_date_lte = timezone.now()
            ).order_by('-pub_date')[:5]
        print(type(s))
        return s

    
class DetailView( generic.DetailView ):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte = timezone.now())

class ResultsView( generic.DetailView ):
    model = Question
    template_name = 'polls/results.html'

# 下面的意思是只有拥有polls.view_choice 权限才可以执行下面的view操作.
#@permission_required_or_403('polls.view_choice', (Choice, 'question_id', 'question_id'))
def vote(request,question_id):
    question = get_object_or_404(Question, pk=question_id)

    try:
        selected_choice = question.choice_set.get( pk = request.POST['inlinechoice'])
    except( KeyError, Choice.DoesNotExist ):
        # Redisplay the question voting form
        return render( request, 'polls/detail.html',
            { 'question':question,
              'error_message':"You didn't select a choice.",
              'adams': 'a test',
            }
        )
    else:
        selected_choice.votes +=1
        selected_choice.save()

        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect( reverse( 'polls:results', args=( question.id,) ) )
