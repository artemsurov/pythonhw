from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponseRedirect
from .models import Question, Choice
from django.views import generic


# Create your views here.
def index(requests):
    question_list = Question.objects.order_by('-pub_data')[:5]
    response = ", "
    for question in question_list:
        response = question.question_text + response
    return render(requests, 'polls/index.html', {'latest_question_list': question_list})


def detail(request, qid):
    question = get_object_or_404(Question, pk=qid)
    return render(request, 'polls/detail.html', {'question': question})


def vote(request, qid):
    question = get_object_or_404(Question, pk=qid)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {'question': question, 'error_message': 'Make your choice bitch'})
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return HttpResponseRedirect(reverse('results', args=(question.id,)))


def results(request, qid):
    question = get_object_or_404(Question, pk=qid)
    return render(request, 'polls/results.html', {'question': question})


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Question.objects.order_by('-pub_data')[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

class ResultView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'
