# Joaquim Werlich Galvão

Site/blog do Joaquim — Chá de Bebê (presentes, fraldas, galeria), preparado para seções futuras.

**Produção:** https://joaquim.werlich.com.br

## Stack

- Python 3 / Django 5
- MariaDB (produção); SQLite opcional em desenvolvimento
- WhiteNoise, Gunicorn, Pillow

## Instalação local

```bash
cd joaquim-werlich-galvao
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Para SQLite local, no .env:
# DB_ENGINE=django.db.backends.sqlite3
python manage.py migrate
python manage.py seed_joaquim
python manage.py createsuperuser
python manage.py runserver
```

Admin: http://127.0.0.1:8000/admin/

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `SECRET_KEY` | Chave Django (obrigatória em produção) |
| `DEBUG` | `1` ou `0` |
| `ALLOWED_HOSTS` | hosts separados por vírgula |
| `CSRF_TRUSTED_ORIGINS` | origens HTTPS |
| `DB_ENGINE` | `django.db.backends.mysql` ou sqlite3 |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | MariaDB |

Não commite `.env` nem `media/`.

## Testes

```bash
python manage.py test apps.cha.tests
```

## Deploy (VPS)

Código em `/var/www/joaquim`, Gunicorn + nginx, domínio `joaquim.werlich.com.br`, certbot SSL.
