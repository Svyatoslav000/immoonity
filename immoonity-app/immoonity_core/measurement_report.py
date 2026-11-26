"""PDF for one calculated measurement, in the language of its interpretation."""

from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import validation
from .interpreter import T

ASSETS = Path(__file__).with_name("report_assets")
TEXT = "ImmoonityReport"
DISPLAY = "ImmoonityReportMedium"
EMAIL = "immoonity@immoonity.ru"
TELEGRAM = "https://t.me/immoonity"
pdfmetrics.registerFont(TTFont(TEXT, str(ASSETS / "report-regular.ttf")))
pdfmetrics.registerFont(TTFont(DISPLAY, str(ASSETS / "report-medium.ttf")))

COPY = {
    "ru": {
        "title": "Отчёт по замеру", "earth": "Предполётная оценка", "flight": "Полётный замер",
        "day": "День полёта", "days": "Плановая длительность миссии", "model": "Версия модели",
        "risk": "Оценка модели", "interval": "90% интервал", "level": "Уровень",
        "inputs": "Введённые показатели", "missing": "Не указано", "anc": "Нейтрофилы", "alc": "Лимфоциты",
        "factors": "Факторы оценки", "what_if": "Что если", "recommendations": "Рекомендации консультанта",
        "no_scenarios": "Для этого замера модель не выделила сценариев с существенным изменением оценки.",
        "limits": "Ограничения", "page": "Страница", "warn": "Проверка входных значений",
        "composite": "Вероятность срыва миссии или клинически подтверждённого иммунодефицита с заболеванием к дню замера пока не оценена.",
        "preview": "Ограниченный предпросмотр",
        "access": "Свяжитесь с командой IMMOONITY, чтобы получить полный доступ к расширенным протоколам.",
    },
    "en": {
        "title": "Measurement report", "earth": "Pre-flight assessment", "flight": "In-flight measurement",
        "day": "Flight day", "days": "Planned mission length", "model": "Model version",
        "risk": "Model estimate", "interval": "90% interval", "level": "Level",
        "inputs": "Entered measurements", "missing": "Not entered", "anc": "Neutrophils", "alc": "Lymphocytes",
        "factors": "Factors in this estimate", "what_if": "What if", "recommendations": "Consultant recommendations",
        "no_scenarios": "The model found no scenarios with a substantial change in this estimate.",
        "limits": "Limitations", "page": "Page", "warn": "Input checks",
        "composite": "The probability of mission failure or clinically confirmed immunodeficiency with disease by the sampling day has not been estimated.",
        "preview": "Restricted preview",
        "access": "Contact the IMMOONITY team for full access to the extended protocols.",
    },
    "zh": {
        "title": "测量报告", "earth": "飞行前评估", "flight": "飞行期间测量",
        "day": "采样飞行日", "days": "计划任务时长", "model": "模型版本",
        "risk": "模型估计值", "interval": "90% 区间", "level": "等级",
        "inputs": "输入的测量值", "missing": "未填写", "anc": "中性粒细胞", "alc": "淋巴细胞",
        "factors": "影响估计的因素", "what_if": "情景分析", "recommendations": "顾问建议",
        "no_scenarios": "模型未发现会明显改变本次估计值的情景。",
        "limits": "局限性", "page": "页", "warn": "输入值核查",
        "composite": "目前尚无法估计截至采样日发生任务失败或临床确诊免疫缺陷并伴具体疾病的概率。",
        "preview": "受限预览", "access": "请联系 IMMOONITY 团队，获取扩展方案的完整访问权限。",
    },
}


def decimal_label(value, lang):
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text.replace(".", ",") if lang == "ru" else text


@lru_cache(maxsize=3)
def preview_image(lang):
    width, height = 1080, 252
    labels = COPY[lang]
    image = Image.new("RGB", (width, height), "#101316")
    draw = ImageDraw.Draw(image)
    backdrop = ImageFont.truetype(str(ASSETS / "report-regular.ttf"), 20)
    for i, label in enumerate(("factors", "inputs", "what_if", "days", "limits", "inputs", "recommendations", "what_if", "level")):
        line = "     ".join((labels[label], labels["access"], labels[label]))
        draw.text((28, 26 * i), line, font=backdrop, fill="#625329" if i in (0, 6) else "#505356")
    image = image.filter(ImageFilter.GaussianBlur(5))
    draw = ImageDraw.Draw(image)
    heading = ImageFont.truetype(str(ASSETS / "report-medium.ttf"), 32)
    body = ImageFont.truetype(str(ASSETS / "report-regular.ttf"), 23)
    draw.line((40, 13, width - 40, 13), fill="#9e8957", width=2)
    draw.text((width / 2, 52), labels["preview"], font=heading, fill="#ffce60", anchor="mm")
    words = labels["access"] if lang == "zh" else labels["access"].split()
    joiner = "" if lang == "zh" else " "
    lines = [""]
    for word in words:
        candidate = joiner.join(filter(None, (lines[-1], word)))
        if draw.textlength(candidate, font=body) > width - 128 and lines[-1]:
            lines.append(word)
        else:
            lines[-1] = candidate
    for i, line in enumerate(lines):
        draw.text((width / 2, 98 + i * 31), line, font=body, fill="#f9fafb", anchor="mm")
    draw.text((width / 2, 175), EMAIL, font=body, fill="#ffce60", anchor="mm")
    draw.text((width / 2, 212), TELEGRAM, font=body, fill="#ffce60", anchor="mm")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class Preview(Flowable):
    def __init__(self, lang):
        super().__init__()
        self.lang = lang
        self.spaceBefore = 12

    def wrap(self, available_width, _height):
        self.width = available_width
        self.height = available_width * 252 / 1080
        return self.width, self.height

    def draw(self):
        self.canv.drawImage(ImageReader(BytesIO(preview_image(self.lang))), 0, 0, self.width, self.height)
        scale = self.width / 1080
        for url, row in (("mailto:" + EMAIL, 175), (TELEGRAM, 212)):
            self.canv.linkURL(url, (315 * scale, (252 - row - 15) * scale,
                                   765 * scale, (252 - row + 15) * scale), relative=1, thickness=0)


def measurement_pdf(prediction, model, day=None, counts=None):
    interpretation = prediction["interpretation"]
    lang = interpretation["language"]
    labels = COPY[lang]
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=19 * mm, bottomMargin=17 * mm, title=labels["title"],
                            author="IMMOONITY", initialFontName=TEXT)
    base = ParagraphStyle("body", fontName=TEXT, fontSize=10, leading=15, spaceAfter=4,
                          textColor=colors.HexColor("#253541"), wordWrap="CJK" if lang == "zh" else None)
    heading = ParagraphStyle("heading", parent=base, fontName=DISPLAY, fontSize=14, leading=19,
                             textColor=colors.HexColor("#704e12"), spaceBefore=10, spaceAfter=5,
                             keepWithNext=True)
    title = ParagraphStyle("title", parent=heading, fontSize=24, leading=32, spaceBefore=0)
    small = ParagraphStyle("small", parent=base, fontSize=9, leading=13)
    rec_heading = ParagraphStyle("recommendation", parent=base, fontName=DISPLAY, spaceBefore=3, spaceAfter=0)

    def para(text, style=base):
        return Paragraph(escape(str(text)), style)

    def show(number):
        return decimal_label(number, lang)

    values = prediction["inputs"]
    interval = prediction["risk_interval"]
    story = [para(labels["title"], title)]
    subtitle = labels[prediction["model"]]
    if day is not None:
        subtitle += "   ·   " + labels["day"] + " " + str(day)
    story.extend([para(subtitle + "   ·   " + labels["model"] + " " + str(prediction["model_version"]), small),
                  para(interpretation["outcome"])])

    def table(rows, widths, first=False):
        data = [[para(cell, small if first and i == 0 else base) for cell in row] for i, row in enumerate(rows)]
        result = Table(data, colWidths=widths, hAlign="LEFT")
        result.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f4f2ed"), colors.white]),
        ]))
        return result

    story.append(table([[labels["risk"], labels["interval"], labels["level"]],
                        [show(prediction["risk"]) + "%", show(interval["low"]) + "–" + show(interval["high"]) + "%",
                         interpretation["level"]["label"]]], [doc.width * .30, doc.width * .36, doc.width * .30], True))
    if interpretation.get("baseline_note"):
        story.append(para(interpretation["baseline_note"]))
    story.append(para(labels["inputs"], heading))
    measurements = []
    for field, spec in model.inputs.items():
        label = labels["days"] if field == "days" else validation.field_label(spec, field, lang)
        unit = validation.unit_label(spec.get("unit"), lang)
        if field == "sex":
            reading = T[lang]["sex"][values[field]]
        else:
            reading = labels["missing"] if field not in values else show(values[field]) + ((" " + unit) if unit else "")
        measurements.append([label, reading])
    if counts:
        unit = {"en": "10⁹/L", "ru": "10⁹/л", "zh": "10⁹/L"}[lang]
        for field in ("anc", "alc"):
            measurements.append([labels[field], show(counts[field]) + " " + unit])
    story.append(table(measurements, [doc.width * .60, doc.width * .36]))
    if prediction.get("input_warnings"):
        story.append(para(labels["warn"], heading))
        story.extend(para(item["message"]) for item in prediction["input_warnings"])
    story.append(para(labels["factors"], heading))
    for item in interpretation.get("drivers", interpretation.get("markers", [])):
        story.append(para(item["text"]))
    for line in interpretation.get("pattern", []):
        story.append(para(line))
    if interpretation.get("duration"):
        story.append(para(interpretation["duration"]))
    story.append(para(labels["what_if"], heading))
    scenarios = [item["text"] for item in interpretation["what_if"]]
    story.extend(para(line) for line in scenarios or [labels["no_scenarios"]])
    story.append(para(labels["recommendations"], heading))
    for item in interpretation["recommendations"]:
        story.append(KeepTogether([para(item["title"], rec_heading), para(item["text"])]))
    story.append(para(labels["limits"], heading))
    if prediction["model"] == "flight" and day is not None:
        story.append(para(labels["composite"], small))
    story.extend(para(note, small) for note in interpretation["notes"])
    story.append(KeepTogether([para(interpretation["disclaimer"], small), Spacer(1, 3 * mm), Preview(lang)]))

    def page_chrome(canvas, document):
        width, height = A4
        canvas.saveState()
        canvas.setFont(DISPLAY, 10)
        canvas.setFillColor(colors.HexColor("#765619"))
        canvas.drawString(18 * mm, height - 13 * mm, "IMMOONITY")
        canvas.setStrokeColor(colors.HexColor("#c7b080"))
        canvas.line(18 * mm, height - 15 * mm, width - 18 * mm, height - 15 * mm)
        canvas.setFont(TEXT, 8)
        canvas.drawRightString(width - 18 * mm, 9 * mm, labels["page"] + " " + str(document.page))
        canvas.restoreState()

    doc.build(story, onFirstPage=page_chrome, onLaterPages=page_chrome)
    return buffer.getvalue()
