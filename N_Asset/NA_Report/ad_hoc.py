from os import path
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_RIGHT


class ReportAdHoc(object):
    def __init__(self, title, sub_title, detail, **kwargs):
        self.name = kwargs.get('name')
        self.receiver = kwargs.get('receiver')
        self.sender = kwargs.get('sender')
        self.equipment = kwargs.get('equipment')
        self.add_equipment = kwargs.get('add_equipment')

        self.title = title
        self.sub_title = sub_title
        self.detail = detail
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(self.buffer, pagesize=A4, title='Report')
        self.layout = [Spacer(1, 0.5 * inch)]
        self.style = getSampleStyleSheet()
        self.image_path = path.join(settings.STATIC_ROOT, 'app', 'images', '')

        self.style.add(
            ParagraphStyle(
                name='sub_title',
                parent=self.style['Normal'],
                fontSize=12,
                leading=16
            )
        )

        self.style.add(
            ParagraphStyle(
                name='detail',
                parent=self.style['Normal'],
                leading=24
            )
        )

        self.style.add(
            ParagraphStyle(
                name='equipment',
                parent=self.style['Normal'],
                fontSize=11,
                leading=14
            )
        )

        self.style.add(
            ParagraphStyle(
                name='signature_left',
                parent=self.style['Normal'],
                alignment=TA_LEFT,
                fontSize=12
            )
        )

        self.style.add(
            ParagraphStyle(
                name='signature_right',
                parent=self.style['Normal'],
                alignment=TA_RIGHT,
                fontSize=12
            )
        )

        self.style.add(
            ParagraphStyle(
                name='grow',
                parent=self.style['Normal'],
                alignment=TA_RIGHT,
                fontSize=15
            )
        )

    def restore_default_canvas(self, canvas):
        canvas.restoreState()
        canvas.saveState()

    def mix_canvas_paragraph(self, canvas, paragraph, **kwargs):
        doc = kwargs.get('doc', self.doc)
        position = kwargs.get('position')
        horizontal = doc.leftMargin
        paragraph.wrap(doc.width, doc.bottomMargin)
        if isinstance(position, tuple):
            horizontal = position[0]
            position = position[1]
        paragraph.drawOn(canvas, horizontal, position)

    def set_canvas_dynamic(self, top):
        len_detail = len(self.detail)
        if len_detail == 10:
            top = top - (len_detail / 50)
        elif len_detail > 10:
            top = top - (len_detail / 25)
        return top

    def create_header(self, canvas, doc):
        w, h = doc.pagesize
        width = 100
        height = 100
        canvas.saveState()
        canvas.drawImage(
            path.join('/' + self.image_path, 'NufarmLogo2.jpg'),
            w - 20 - width,
            h - 20 - height,
            width=width,
            height=height
        )
        canvas.restoreState()

    def create_title(self):
        self.layout.append(Spacer(0, 15))
        self.layout.append(
            Paragraph(self.title, self.style['Title'])
        )

    def create_sub_title(self):
        self.layout.append(
            Paragraph(self.sub_title, self.style['sub_title'])
        )

    def create_detail(self):
        self.layout.append(Spacer(0, 20))
        detail = Table(
            [(key, ': {value}'.format(value=value)) for key, value in self.detail.items()],
            hAlign='LEFT'
        )
        print(detail.wrap(0,0))
        self.layout.append(detail)

    def create_equipment(self):
        self.layout.append(Spacer(0, 20))
        self.layout.append(
            Paragraph('<b>Perlengkapan standar :</b>', self.style['equipment'])
        )
        equipment_list = self.equipment
        for equipment in equipment_list:
            self.layout.append(
                Paragraph(equipment, self.style['equipment'], bulletText=u'\u27a4')
            )

    def create_add_equipment(self):
        self.layout.append(Spacer(0, 20))
        self.layout.append(
            Paragraph('<b>Perlengkapan tambahan :</b>', self.style['equipment'])
        )
        add_equipment_list = self.add_equipment
        for add_equipment in add_equipment_list:
            self.layout.append(
                Paragraph(add_equipment, self.style['equipment'], bulletText=u'\u27a4')
            )

    def create_signature(self, canvas, doc, **kwargs):
        receiver = "Yang Menerima,"
        receiver = Paragraph(receiver, self.style['signature_left'])
        self.mix_canvas_paragraph(
            canvas=canvas,
            paragraph=receiver,
            position=3 * inch
        )

        receiver_name = kwargs.get('receiver_name')
        receiver_name = Paragraph(receiver_name, self.style['signature_left'])
        self.mix_canvas_paragraph(
            canvas=canvas,
            paragraph=receiver_name,
            position=1.8 * inch
        )

        sender = "Yang Menyerahkan,"
        sender = Paragraph(sender, self.style['signature_right'])
        self.mix_canvas_paragraph(
            canvas=canvas,
            paragraph=sender,
            position=3 * inch
        )

        sender_name = kwargs.get('sender_name')
        sender_name = Paragraph(sender_name, self.style['signature_right'])
        self.mix_canvas_paragraph(
            canvas=canvas,
            paragraph=sender_name,
            position=1.8 * inch
        )

    def create_footer(self, canvas, doc):
        canvas.saveState()
        text = "Demikian Berita Acara ini dibuat dengan sebenarnya"
        top = self.set_canvas_dynamic(4.1)
        canvas.drawString(inch, top * inch, text)
        tgl = "Jakarta, 14 Desember 2016"
        canvas.setFont('Helvetica-Bold', 13)
        top = self.set_canvas_dynamic(3.8)
        canvas.drawString(inch, top * inch, tgl)
        self.create_signature(
            canvas=canvas,
            doc=doc,
            receiver_name='<b>{receiver}</b>'.format(
                receiver=self.receiver
            ),
            sender_name='<b>{sender}</b>'.format(
                sender=self.sender
            )
        )
        grow = "<b><font color='green'>Grow a better tomorrow.</font></b>"
        grow = Paragraph(grow, self.style['grow'])
        self.mix_canvas_paragraph(
            canvas=canvas,
            paragraph=grow,
            position=((1.5 * inch), (0.5 * inch))
        )
        canvas.restoreState()

    def first_page(self, canvas, doc):
        self.create_header(canvas, doc)
        if doc.page > 1:
            return
        return self.create_footer(canvas, doc)

    def last_page(self, canvas, doc):
        if doc.page > 1:
            return self.create_footer(canvas, doc)
        return self.create_header(canvas, doc)

    def write_pdf_view(self):
        self.create_title()
        self.create_sub_title()
        self.create_detail()

        if self.equipment:
            self.create_equipment()

        if self.add_equipment:
            self.create_add_equipment()

        self.doc.build(
            self.layout,
            onFirstPage=self.first_page,
            onLaterPages=self.last_page
        )

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="{file_name}.pdf"'.format(
            file_name=self.name
        )
        response.write(self.buffer.getvalue())
        self.buffer.close()
        return response
