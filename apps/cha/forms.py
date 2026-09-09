from django import forms


class GiftReservationForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, required=False, initial=1, label='Quantidade')
    guest_name = forms.CharField(max_length=120, required=False, label='Seu nome')
    item_name = forms.CharField(max_length=160, required=False, label='Qual presente você vai levar?')
    is_anonymous = forms.BooleanField(required=False, label='Prefiro aparecer como Anônimo')
    message = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 3}),
        label='Mensagem para o Joaquim (opcional)',
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('is_anonymous') and not (cleaned.get('guest_name') or '').strip():
            self.add_error('guest_name', 'Informe seu nome ou marque Anônimo.')
        qty = cleaned.get('quantity')
        if qty is None:
            cleaned['quantity'] = 1
        return cleaned


class DiaperPledgeForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label='Quantidade de pacotes')
    guest_name = forms.CharField(max_length=120, required=False, label='Seu nome')
    is_anonymous = forms.BooleanField(required=False, label='Prefiro aparecer como Anônimo')
    message = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 3}),
        label='Mensagem para o Joaquim (opcional)',
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('is_anonymous') and not (cleaned.get('guest_name') or '').strip():
            self.add_error('guest_name', 'Informe seu nome ou marque Anônimo.')
        return cleaned


class ChaRegisterForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        label='Seu nome',
        widget=forms.TextInput(attrs={
            'autocomplete': 'name',
            'placeholder': 'Seu nome',
        }),
    )
    password = forms.CharField(
        min_length=4,
        max_length=64,
        label='Crie uma senha',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Crie uma senha',
        }),
    )
    password_confirm = forms.CharField(
        min_length=4,
        max_length=64,
        label='Confirme a senha',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Confirme a senha',
        }),
    )

    def clean_name(self):
        from .models import ChaGuest
        name = ChaGuest.normalize_name(self.cleaned_data.get('name') or '')
        if not name:
            raise forms.ValidationError('Informe seu nome.')
        return name

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password') or ''
        conf = cleaned.get('password_confirm') or ''
        if pwd and conf and pwd != conf:
            self.add_error('password_confirm', 'As senhas não coincidem.')
        return cleaned


class ChaLoginForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        label='Seu nome',
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'placeholder': 'Seu nome',
        }),
    )
    password = forms.CharField(
        max_length=64,
        label='Sua senha',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Sua senha',
        }),
    )

    def clean_name(self):
        from .models import ChaGuest
        name = ChaGuest.normalize_name(self.cleaned_data.get('name') or '')
        if not name:
            raise forms.ValidationError('Informe seu nome.')
        return name


class ChaRsvpForm(forms.Form):
    response = forms.ChoiceField(
        choices=[
            ('sim', 'Sim'),
            ('talvez', 'Talvez'),
            ('nao', 'Não poderei'),
        ],
    )
    name = forms.CharField(max_length=120, required=False)
    companions = forms.IntegerField(min_value=0, required=False, initial=0)

    def clean(self):
        cleaned = super().clean()
        resp = cleaned.get('response')
        if resp in ('sim', 'talvez') and not (cleaned.get('name') or '').strip():
            self.add_error('name', 'Informe seu nome.')
        if resp == 'nao':
            cleaned['companions'] = 0
        elif cleaned.get('companions') is None:
            cleaned['companions'] = 0
        return cleaned
