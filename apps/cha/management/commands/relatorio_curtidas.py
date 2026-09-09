"""Gera em PDF o relatório de curtidas: situação vigente + histórico completo."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.cha.models import ChaGuest, GiftReservation, ReservationLike

VERDE = colors.HexColor('#7AAB97')
TINTA = colors.HexColor('#3A423E')
CREME = colors.HexColor('#F1F7F4')
BORDA = colors.HexColor('#DDE6E1')

_styles = getSampleStyleSheet()
H1 = ParagraphStyle('h1', parent=_styles['Title'], textColor=TINTA, fontSize=19, spaceAfter=4)
SUB = ParagraphStyle('sub', parent=_styles['Normal'], textColor=colors.HexColor('#6F776F'),
                     fontSize=9.5, alignment=1, spaceAfter=16)
H2 = ParagraphStyle('h2', parent=_styles['Heading2'], textColor=TINTA, fontSize=12.5,
                    spaceBefore=12, spaceAfter=7)
TXT = ParagraphStyle('txt', parent=_styles['Normal'], textColor=TINTA, fontSize=10, leading=14.5)
CEL = ParagraphStyle('cel', parent=_styles['Normal'], textColor=TINTA, fontSize=9, leading=11.5)


def _fmt(dt):
    if not dt:
        return '—'
    return timezone.localtime(dt).strftime('%d/%m/%Y %H:%M')


def _tabela(dados, larguras):
    tabela = Table(dados, colWidths=larguras, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TINTA),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CREME]),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
    ]))
    return tabela


class Command(BaseCommand):
    help = 'Gera o PDF de curtidas (vigentes + histórico).'

    def add_arguments(self, parser):
        parser.add_argument('--out', default='curtidas.pdf', help='Caminho do PDF de saída.')

    def handle(self, *args, **options):
        destino = options['out']
        curtidas = list(
            ReservationLike.objects.select_related(
                'guest', 'reservation', 'reservation__gift'
            ).order_by('created_at', 'id')
        )
        vigentes = [lk for lk in curtidas if lk.is_current]

        doc = SimpleDocTemplate(
            destino, pagesize=A4, title='Curtidas — Chá de Bebê do Joaquim',
            leftMargin=1.8 * cm, rightMargin=1.8 * cm,
            topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        )
        story = [
            Paragraph('Curtidas das escolhas de presente', H1),
            Paragraph(
                'Chá de Bebê do Joaquim Werlich Galvão · relatório de '
                + timezone.localtime().strftime('%d/%m/%Y às %H:%M'),
                SUB,
            ),
        ]

        story.append(Paragraph(f'Curtidas vigentes ({len(vigentes)})', H2))
        if vigentes:
            dados = [['Quem curtiu', 'Presente', 'Escolhido por', 'Curtiu em']]
            for lk in vigentes:
                dados.append([
                    Paragraph(lk.guest.name, CEL),
                    Paragraph(lk.reservation.gift.name, CEL),
                    Paragraph(lk.reservation.display_name, CEL),
                    _fmt(lk.created_at),
                ])
            story.append(_tabela(dados, [4.6 * cm, 5 * cm, 4 * cm, 3.2 * cm]))
        else:
            story.append(Paragraph('Nenhuma curtida vigente no momento.', TXT))

        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph(f'Histórico completo ({len(curtidas)})', H2))
        if curtidas:
            dados = [['Quem', 'Presente', 'Curtiu em', 'Descurtiu em', 'Situação']]
            for lk in curtidas:
                dados.append([
                    Paragraph(lk.guest.name, CEL),
                    Paragraph(lk.reservation.gift.name, CEL),
                    _fmt(lk.created_at),
                    _fmt(lk.removed_at),
                    'Vigente' if lk.is_current else 'Removida',
                ])
            story.append(_tabela(dados, [4 * cm, 4.4 * cm, 3.1 * cm, 3.1 * cm, 2.2 * cm]))
        else:
            story.append(Paragraph(
                'Nenhum registro de curtida até agora. O histórico guarda também as '
                'curtidas desfeitas, com a data em que foram removidas.', TXT))

        story.append(Spacer(1, 0.35 * cm))
        story.append(Paragraph('Curtidas por escolha', H2))
        reservas = (
            GiftReservation.objects.filter(cancelled_at__isnull=True)
            .select_related('gift').order_by('created_at')
        )
        dados = [['Presente', 'Escolhido por', 'Escolhido em', 'Vigentes', 'Já curtiram']]
        for r in reservas:
            registros = [lk for lk in curtidas if lk.reservation_id == r.pk]
            dados.append([
                Paragraph(r.gift.name, CEL),
                Paragraph(r.display_name, CEL),
                _fmt(r.created_at),
                str(sum(1 for lk in registros if lk.is_current)),
                str(len({lk.guest_id for lk in registros})),
            ])
        story.append(_tabela(dados, [4.9 * cm, 3.9 * cm, 3.1 * cm, 2 * cm, 2.9 * cm]))

        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph(
            f'Convidados com nome e senha cadastrados: <b>{ChaGuest.objects.count()}</b> — '
            'só eles podem curtir, uma vez por escolha. Descurtir não apaga o registro: '
            'a linha fica no histórico com a data da remoção. Consulta ao vivo no admin, '
            'em <b>Chá &gt; Curtidas</b>.', TXT))

        doc.build(story)
        self.stdout.write(self.style.SUCCESS(f'PDF gerado em {destino}'))
