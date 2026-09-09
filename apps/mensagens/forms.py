from django import forms
from django.utils.html import strip_tags

from .models import Recado


class RecadoForm(forms.Form):
    nome = forms.CharField(
        max_length=100,
        label='Seu nome',
        widget=forms.TextInput(attrs={
            'autocomplete': 'name',
            'placeholder': 'Como você gostaria de aparecer',
            'maxlength': '100',
        }),
    )
    relacao = forms.ChoiceField(
        required=False,
        label='Quem é você na história do Joaquim?',
        choices=[('', 'Opcional')] + list(Recado.RELACAO_CHOICES),
        widget=forms.Select(attrs={'autocomplete': 'off'}),
    )
    mensagem = forms.CharField(
        min_length=1,
        max_length=1000,
        label='Seu recado',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'maxlength': '1000',
            'placeholder': 'Escreva aqui uma mensagem para o Joaquim...',
        }),
    )
    email = forms.EmailField(
        required=False,
        label='E-mail (opcional)',
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'Só a família vê, se precisar falar com você',
        }),
    )
    website = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'autocomplete': 'off',
            'tabindex': '-1',
            'aria-hidden': 'true',
        }),
    )

    def is_honeypot(self) -> bool:
        return bool((self.data.get('website') or '').strip())

    def clean_nome(self) -> str:
        nome = strip_tags(self.cleaned_data.get('nome') or '').strip()
        if not nome:
            raise forms.ValidationError('Informe seu nome.')
        return nome[:100]

    def clean_mensagem(self) -> str:
        texto = strip_tags(self.cleaned_data.get('mensagem') or '').strip()
        if not texto:
            raise forms.ValidationError('Escreva um recadinho para o Joaquim.')
        if len(texto) > 1000:
            raise forms.ValidationError('O recado pode ter no máximo 1000 caracteres.')
        return texto

    def clean_email(self) -> str:
        return (self.cleaned_data.get('email') or '').strip()

    def clean_relacao(self) -> str:
        value = (self.cleaned_data.get('relacao') or '').strip()
        allowed = {code for code, _label in Recado.RELACAO_CHOICES}
        if value and value not in allowed:
            return ''
        return value

    def save(self) -> Recado:
        return Recado.objects.create(
            nome=self.cleaned_data['nome'],
            mensagem=self.cleaned_data['mensagem'],
            email=self.cleaned_data.get('email') or '',
            relacao=self.cleaned_data.get('relacao') or '',
            status=Recado.STATUS_PENDING,
        )
