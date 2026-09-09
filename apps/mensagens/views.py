from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .antispam import is_rate_limited, register_submission
from .forms import RecadoForm
from .models import Recado

PAGE_SIZE = 12


@require_http_methods(['GET', 'POST'])
def recadinhos(request):
    form = RecadoForm()
    if request.method == 'POST':
        form = RecadoForm(request.POST)
        if form.is_honeypot():
            return redirect(f"{reverse('recadinhos')}?enviado=1")
        if is_rate_limited(request):
            messages.error(
                request,
                'Você já enviou alguns recadinhos agora. '
                'Tente de novo daqui a pouco 💚',
            )
            return redirect(reverse('recadinhos') + '#escrever')
        if form.is_valid():
            form.save()
            register_submission(request)
            return redirect(f"{reverse('recadinhos')}?enviado=1")

    page_obj = Paginator(
        Recado.objects.approved(),
        PAGE_SIZE,
    ).get_page(request.GET.get('page'))

    return render(request, 'mensagens/recadinhos.html', {
        'form': form,
        'page_obj': page_obj,
        'recados': page_obj.object_list,
        'enviado': request.GET.get('enviado') == '1',
    })
