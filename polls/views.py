from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.template.defaultfilters import pluralize
from django.middleware.csrf import get_token

from lys import L, render as render_lys

from .models import Choice, Question

class MixinLysResponse:
    """
    Override render_to_response() to render via self.template()
    """

    def render_to_response(self, context):
        return HttpResponse(render_lys(self.template(
            **context
        )))


class IndexView(MixinLysResponse, generic.ListView):
    context_object_name = 'latest_question_list'

    def template(self, latest_question_list, **context):
        return (
            L.link(rel='stylesheet', href=static('polls/style.css')),
            (
                L.ul / (
                    (
                        L.li / (
                            L.a(href=reverse('polls:detail', args=(question.id,))) / question.question_text
                        )
                    ) for question in latest_question_list
                )
            ) if latest_question_list else (
                L.p / 'No polls are available.'
            )
        )

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]


class DetailView(MixinLysResponse, generic.DetailView):
    model = Question

    def template(self, question, error_message=None, **context):
        return (
            (
                L.p / (
                    L.strong / error_message
                )
            ) if error_message else None,
            L.form(action=reverse('polls:vote', args=(question.id,)), method='post') / (
                L.input(type='hidden', name='csrfmiddlewaretoken', value=get_token(self.request)),
                (
                    (
                        L.input(type='radio', name='choice', id='choice%d' % i, value=str(choice.id)),
                        L.label(for_='choice%d') / choice.choice_text,
                        L.br
                    ) for i, choice in enumerate(question.choice_set.all())
                ),
                L.input(type='submit', value='vote')
            )
        )

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(MixinLysResponse, generic.DetailView):
    model = Question

    def template(self, question, **context):
        return (
            L.h1 / question.question_text,
            L.ul / (
                (
                    L.li / (
                        "%s -- %s vote%s" % (choice.choice_text, choice.votes, pluralize(choice.votes))
                    )
                ) for choice in question.choice_set.all()
            ),
            L.a(href=reverse('polls:detail', args=(question.id,))) / 'Vote again?',
        )


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return DetailView(request=request).render_to_response(context={
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
