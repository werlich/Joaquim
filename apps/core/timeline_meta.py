"""Metadados visuais da timeline — sem alterar o banco."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable

MONTHS_LONG = (
    '',
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
)
MONTHS_SHORT = (
    '',
    'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
    'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ',
)

CHAPTERS = {
    'antes': {
        'title': 'Antes de mim',
        'mark': '🌿',
    },
    'cheguei': {
        'title': 'Eu cheguei',
        'mark': '💚',
    },
    'coracao': {
        'title': 'Meu coração começou a bater',
        'mark': '💓',
    },
    'trimestre1': {
        'title': 'Estou crescendo',
        'mark': '👶',
    },
    'trimestre2': {
        'title': 'Minha família está me esperando',
        'mark': '🏡',
    },
    'cha': {
        'title': 'Meu Chá de Bebê',
        'mark': '🎁',
    },
    'nascimento': {
        'title': 'O grande dia chegou',
        'mark': '✨',
    },
}

_DATE_PREFIX = re.compile(r'^\s*\d{1,2}/\d{1,2}(?:/\d{2,4})?\s*[-–—]\s*')


def _text(entry) -> str:
    parts = [getattr(entry, 'title', '') or '', getattr(entry, 'body', '') or '']
    return ' '.join(parts).lower()


def chapter_key(entry) -> str:
    text = _text(entry)
    if 'chá de bebê' in text or 'cha de bebe' in text:
        return 'cha'
    if 'nascimento' in text or re.search(r'\bnasci\b', text):
        return 'nascimento'
    if 'conheci minha família' in text or 'conheci minha familia' in text:
        return 'nascimento'
    d = entry.event_date
    if d < date(2026, 5, 2):
        return 'antes'
    if d == date(2026, 5, 2) or 'grávida' in text or 'gravida' in text:
        return 'cheguei'
    if (
        d == date(2026, 5, 14)
        or 'primeira ecografia' in text
        or 'coraçãozinho' in text
        or 'coracaozinho' in text
    ):
        return 'coracao'
    if d <= date(2026, 6, 30):
        return 'trimestre1'
    return 'trimestre2'


def is_featured(entry) -> bool:
    text = _text(entry)
    if 'chá de bebê' in text or 'cha de bebe' in text:
        return True
    if 'morfológica' in text or 'morfologica' in text:
        return True
    if 'primeira ecografia' in text or 'coraçãozinho' in text or 'coracaozinho' in text:
        return True
    if 'grávida' in text or 'gravida' in text:
        return True
    if 'nascimento' in text or re.search(r'\bnasci\b', text):
        return True
    if 'conheci minha família' in text or 'conheci minha familia' in text:
        return True
    if re.search(r'(era um menino|sou um menino|sexo masculino)', text):
        return True
    return False


def is_birth(entry) -> bool:
    return chapter_key(entry) == 'nascimento'


def kind_for(entry) -> str:
    text = _text(entry)
    if any(k in text for k in (
        'ecografia', 'morfológica', 'morfologica', 'teste', 'exame',
    )):
        return 'exam'
    if 'presente' in text:
        return 'gift'
    if any(k in text for k in (
        'marley', 'irmãozinho', 'irmaozinho', 'irmãozinhos', 'irmaozinhos',
        'cães', 'caes', 'pelud', 'banheira',
    )):
        return 'pets'
    if entry.event_date < date(2026, 5, 2):
        return 'pets' if any(k in text for k in ('irmão', 'irmao', 'jesus')) else 'family'
    if any(k in text for k in (
        'família', 'familia', 'vovó', 'vovo', 'vovô', 'vovozinho',
        'titia', 'papais', 'dia dos pais',
    )):
        return 'family'
    if 'curso' in text:
        return 'event'
    if any(k in text for k in ('barriga', 'semanas', 'solzinho', 'crescendo')):
        return 'growth'
    if any(k in text for k in ('grávida', 'gravida', 'coraçãozinho', 'menino')):
        return 'special'
    return 'photo'


def photos_fit(kind: str) -> str:
    return 'contain' if kind == 'exam' else 'cover'


def display_title(entry) -> str:
    title = (entry.title or '').strip()
    if title:
        return title
    text = _text(entry)
    if 'primeira ecografia' in text:
        return 'Primeira ecografia'
    if 'segunda ecografia' in text:
        return 'Segunda ecografia'
    if 'morfológica de segundo' in text or 'morfologica de segundo' in text:
        return 'Morfológica 2º trimestre'
    if 'morfológica de primeiro' in text or 'morfologica de primeiro' in text:
        return 'Morfológica 1º trimestre'
    if 'grávida' in text or 'gravida' in text:
        return 'A descoberta'
    if 'era um menino' in text:
        return 'É um menino'
    if 'sou um menino' in text:
        return 'Certeza: menino'
    if 'presente' in text:
        return 'Primeiro presente'
    if 'titia' in text:
        return 'Vovó e titia Manu'
    if 'vovôzinho' in text or 'vovozinho' in text:
        return 'Meu vovôzinho'
    if 'banheira' in text:
        return 'A banheira'
    if 'dia dos pais' in text:
        return 'Dia dos pais'
    if 'curso' in text:
        return 'O curso'
    if 'solzinho' in text:
        return 'Solzinho'
    if 'irmãozinhos' in text or 'irmaozinhos' in text:
        return 'Os irmãozinhos'
    if 'marley' in text:
        return 'Marley'
    if 'família' in text or 'familia' in text:
        return 'Minha família'
    if 'eu e minha mamãe' in text or 'eu e minha mamae' in text:
        return 'Eu e mamãe'
    if 'primeira fotinho' in text or '8 semanas' in text:
        return 'Primeira fotinho'
    if 'grandinha' in text:
        return 'Barriga grandinha'
    if 'barriga' in text:
        return 'A barriga'
    if 'irmãozinho' in text or 'irmaozinho' in text or 'cães' in text or 'caes' in text:
        return 'Os irmãozinhos'
    if 'se conheceram' in text or getattr(entry.event_date, 'year', 2026) < 2026:
        return 'Papai e mamãe'
    body = _DATE_PREFIX.sub('', display_body(entry).strip())
    if not body:
        return entry.display_date() if hasattr(entry, 'display_date') else ''
    first = re.split(r'[.!?\n]', body, maxsplit=1)[0].strip()
    if len(first) > 36:
        return first[:33].rstrip() + '…'
    return first


def display_body(entry) -> str:
    body = entry.body or ''
    return body.replace('há quase 15 anos atrás', 'há quase 15 anos')


def _norm_copy(text: str) -> str:
    text = _DATE_PREFIX.sub('', (text or '').strip())
    text = re.sub(r'\s+', ' ', text)
    return text.rstrip(' .!?…').casefold().strip()


def body_if_not_duplicate(title: str, body: str) -> str:
    """Hide the paragraph when it repeats the title exactly."""
    if not (body or '').strip():
        return ''
    if _norm_copy(body) == _norm_copy(title):
        return ''
    return body


def date_badge(entry) -> str:
    label = (entry.date_label or '').strip()
    if label:
        return label
    d = entry.event_date
    return f'{d.day:02d} {MONTHS_SHORT[d.month]} {d.year}'


def range_label(entries: Iterable) -> str:
    dated = [e.event_date for e in entries if getattr(e, 'event_date', None)]
    if not dated:
        return ''
    start = min((d for d in dated if d.year >= 2026), default=min(dated))
    return f'{MONTHS_LONG[start.month]} de {start.year} → hoje'


def moment_count_label(n: int) -> str:
    if n == 1:
        return '1 momento registrado'
    return f'{n} momentos registrados'


@dataclass
class TimelineMoment:
    entry: object
    chapter: str
    chapter_title: str
    chapter_mark: str
    show_chapter: bool
    featured: bool
    is_birth: bool
    kind: str
    fit: str
    side: str
    display_title: str
    display_body: str
    date_badge: str
    photos: list = field(default_factory=list)
    extra_photos: int = 0
    familia_anchor: bool = False

    @property
    def pk(self):
        return self.entry.pk

    @property
    def event_date(self):
        return self.entry.event_date

    def display_date(self):
        return self.entry.display_date()


def annotate(entries) -> tuple[list[TimelineMoment], list[dict], str, str]:
    items = list(entries)
    moments: list[TimelineMoment] = []
    last_chapter = None
    side_i = 0
    familia_set = False

    for entry in items:
        key = chapter_key(entry)
        meta = CHAPTERS[key]
        featured = is_featured(entry)
        kind = kind_for(entry)
        photos = list(entry.photos()) if hasattr(entry, 'photos') else []
        extra = max(0, len(photos) - 4)
        if featured:
            side = 'full'
        else:
            side = 'left' if side_i % 2 == 0 else 'right'
            side_i += 1
        show_chapter = key != last_chapter
        last_chapter = key
        familia_anchor = False
        if (
            not familia_set
            and entry.event_date >= date(2026, 5, 2)
            and kind in ('family', 'pets')
        ):
            familia_anchor = True
            familia_set = True
        title = display_title(entry)
        body = body_if_not_duplicate(title, display_body(entry))
        moments.append(TimelineMoment(
            entry=entry,
            chapter=key,
            chapter_title=meta['title'],
            chapter_mark=meta['mark'],
            show_chapter=show_chapter,
            featured=featured,
            is_birth=is_birth(entry),
            kind=kind,
            fit=photos_fit(kind),
            side=side,
            display_title=title,
            display_body=body,
            date_badge=date_badge(entry),
            photos=photos,
            extra_photos=extra,
            familia_anchor=familia_anchor,
        ))

    present = {m.chapter for m in moments}
    nav: list[dict] = []
    if not moments:
        return moments, nav, moment_count_label(0), ''
    nav = [{'href': '#journey-top', 'label': 'Toda história'}]
    if 'antes' in present:
        nav.append({'href': '#capitulo-antes', 'label': 'Antes de mim'})
    t1 = next((c for c in ('cheguei', 'coracao', 'trimestre1') if c in present), None)
    if t1:
        nav.append({'href': f'#capitulo-{t1}', 'label': '1º trimestre'})
    if 'trimestre2' in present:
        nav.append({'href': '#capitulo-trimestre2', 'label': '2º trimestre'})
        if any(m.familia_anchor for m in moments):
            nav.append({'href': '#capitulo-familia', 'label': 'Família'})
        else:
            nav.append({'href': '#capitulo-trimestre2', 'label': 'Família'})
    if 'cha' in present:
        nav.append({'href': '#capitulo-cha', 'label': 'Chá de bebê'})
    if 'nascimento' in present:
        nav.append({'href': '#capitulo-nascimento', 'label': 'O grande dia'})

    count_label = moment_count_label(len(moments))
    span = range_label(items)
    return moments, nav, count_label, span
