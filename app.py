"""
Flask-приложение для генерации резюме соискателя вакансии.

Генерация использует шаблоны фраз с вариантами.
Для каждого блока текста предусмотрено 3 семантически близких варианта,
которые выбираются случайным образом при каждой генерации.
"""

import os
import re
import random
import json
import io
import ssl
import urllib.request
import urllib.parse
from fpdf import FPDF
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

try:
    from config import VK_GROUP_ID, VK_TOKEN
except ImportError:
    VK_GROUP_ID = ''
    VK_TOKEN = ''

# ---------------------------------------------------------------------------
# Шаблоны фраз — загружаются из answers.json
# Структура: стиль → возраст → блок → [3 варианта]
# ---------------------------------------------------------------------------
with open('answers.json', encoding='utf-8') as _f:
    TEMPLATES = json.load(_f)
# Утилиты
# ---------------------------------------------------------------------------


def count_significant_chars(text):
    """Подсчёт букв и цифр без пробелов и знаков препинания."""
    return len(re.sub(r'[\W_]', '', text))


def validate_input(data):
    """
    Проверяет корректность входных данных формы.

    Returns:
        tuple: (is_valid, error_message)
    """
    name = data.get('name', '').strip()
    vacancy = data.get('vacancy', '').strip()
    competencies = data.get('competencies', '').strip()
    age = data.get('age', '')
    style = data.get('style', '')

    if not all([name, vacancy, competencies, age, style]):
        return False, 'заполните все поля'

    fields_to_check = [
        (name, 'имя'),
        (vacancy, 'название вакансии'),
        (competencies, 'компетенции'),
    ]

    for field, field_name in fields_to_check:
        letters = [c for c in field if c.isalpha()]
        if len(letters) < 2:
            return False, 'введите осмысленную информацию'
        unique_letters = set(l.lower() for l in letters)
        if len(unique_letters) < 2 and len(field) > 2:
            return False, 'введите осмысленную информацию'

    return True, None


def make_bullets(items):
    """Формирует список компетенций с маркерами."""
    return '\n'.join(f'• {c}' for c in items)


# ---------------------------------------------------------------------------
# Генерация резюме со случайным выбором вариантов фраз
# ---------------------------------------------------------------------------


def generate_resume(name, vacancy, competencies, age, style):
    """
    Собирает текст резюме из блоков шаблонов.

    Для каждого блока случайно выбирается один из трёх вариантов.
    """
    template = TEMPLATES[style]

    title = random.choice(template['title']).format(name=name, vacancy=vacancy)

    age_data = template['main'][age]
    comps_bullets = make_bullets(competencies)
    comps_str = ', '.join(competencies)

    main_parts = []
    for block_key in ('intro', 'skills', 'approach', 'goals'):
        variant = random.choice(age_data[block_key])
        main_parts.append(
            variant.format(
                name=name, vacancy=vacancy,
                comps_bullets=comps_bullets, comps_str=comps_str,
            )
        )

    main_text = '\n\n'.join(main_parts)

    adv_parts = []
    for adv_block in template['advantages']:
        adv_parts.append(random.choice(adv_block))
    advantages = 'Мои основные преимущества как кандидата:\n\n' + '\n\n'.join(
        f'{i + 1}. {text}' for i, text in enumerate(adv_parts)
    )

    return f'{title}\n\n{main_text}\n\n{advantages}'


def adjust_text_length(text, min_chars=1500, max_chars=5000):
    """Корректирует длину текста до заданных границ."""
    sig_chars = count_significant_chars(text)

    if sig_chars < min_chars:
        filler = (
            '\n\nЯ ответственно отношусь к своим профессиональным обязанностям, '
            'выполняю работу качественно и в установленные сроки. Моя цель — '
            'приносить пользу компании и реализовывать свой потенциал '
            'в выбранной сфере деятельности.'
        )
        while count_significant_chars(text) < min_chars:
            text += filler

    elif sig_chars > max_chars:
        words = text.split()
        trimmed = []
        for word in words:
            candidate = ' '.join(trimmed + [word])
            if count_significant_chars(candidate) < max_chars - 100:
                trimmed.append(word)
            else:
                break
        text = ' '.join(trimmed)

    return text


# ---------------------------------------------------------------------------
# Маршруты Flask
# ---------------------------------------------------------------------------


@app.route('/')
def index():
    """Главная страница с формой."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Принимает данные формы, возвращает сгенерированное резюме."""
    data = request.get_json()

    is_valid, error_message = validate_input(data)
    if not is_valid:
        return jsonify({'text': error_message})

    name = data['name'].strip()
    vacancy = data['vacancy'].strip()
    competencies = [c.strip() for c in data['competencies'].split(',') if c.strip()]
    age = data['age']
    style = data['style']

    resume_text = generate_resume(name, vacancy, competencies, age, style)
    resume_text = adjust_text_length(resume_text)

    return jsonify({'text': resume_text})


@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Принимает текст, возвращает PDF-файл для скачивания."""
    if request.is_json:
        text = request.get_json().get('text', '')
    else:
        text = request.form.get('text', '')

    pdf = FPDF()
    pdf.add_page()

    font_candidates = [
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/calibri.ttf',
        'C:/Windows/Fonts/times.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)
    if font_path is None:
        for root, dirs, files in os.walk('/usr/share/fonts'):
            for f in files:
                if f.endswith('.ttf'):
                    font_path = os.path.join(root, f)
                    break
            if font_path:
                break
    if font_path is None:
        return jsonify({'error': 'не найден системный шрифт для PDF'}), 500
    pdf.add_font('CustomFont', '', font_path)
    pdf.set_font('CustomFont', '', 11)
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.multi_cell(0, 5.5, text)

    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)

    return Response(
        buf.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': 'attachment; filename="resume.pdf"',
            'Content-Length': str(buf.getbuffer().nbytes),
        }
    )


@app.route('/post-to-vk', methods=['POST'])
def post_to_vk():
    """Публикует текст резюме на стене сообщества ВКонтакте."""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'сначала сгенерируйте резюме'}), 400
    if not VK_TOKEN or not VK_GROUP_ID:
        return jsonify({'error': 'VK не настроен. Заполните VK_TOKEN и VK_GROUP_ID в config.py'}), 400

    params = urllib.parse.urlencode({
        'owner_id': f'-{VK_GROUP_ID}',
        'message': text,
        'access_token': VK_TOKEN,
        'v': '5.131',
    }).encode()

    req = urllib.request.Request(
        'https://api.vk.com/method/wall.post',
        data=params,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ssl._create_unverified_context())
        result = json.loads(resp.read().decode('utf-8'))

        if 'error' in result:
            return jsonify({'error': result['error']['error_msg']}), 400

        post_id = result.get('response', {}).get('post_id')
        return jsonify({
            'post_id': post_id,
            'url': f'https://vk.com/public{VK_GROUP_ID}?w=wall-{VK_GROUP_ID}_{post_id}'
        })

    except urllib.error.URLError as e:
        return jsonify({'error': f'ошибка сети: {e.reason}'}), 500
    except Exception as e:
        return jsonify({'error': f'неизвестная ошибка: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
