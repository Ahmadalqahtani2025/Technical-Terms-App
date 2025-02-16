from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from gtts import gTTS
from werkzeug.utils import secure_filename
import json
import random
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# التأكد من وجود المجلدات الضرورية
def ensure_directories():
    directories = [
        'static/images',
        'static/audio',
        'static/css',
        'static/js',
        'templates/games',
        'static/images/tools',
        'static/images/parts',
        'static/images/actions',
        'static/images/safety',
        'static/images/specializations/mechanics',
        'static/images/specializations/electricity',
        'static/images/specializations/programming',
        'static/images/specializations/networking',
        'static/images/specializations/hardware',
        'static/images/specializations/security'
    ]
    for directory in directories:
        os.makedirs(os.path.join(app.root_path, directory), exist_ok=True)

ensure_directories()

def load_terms():
    try:
        with open('terms.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_terms(terms):
    with open('terms.json', 'w', encoding='utf-8') as f:
        json.dump(terms, f, ensure_ascii=False, indent=4)

# تحميل المصطلحات
terms = load_terms()

def get_term_image(term):
    """الحصول على مسار الصورة للمصطلح"""
    if not term or not isinstance(term, dict):
        return url_for('static', filename='images/placeholder.png')

    # تحويل المصطلح إلى صيغة اسم الملف
    english_term = term['English Term'].lower()
    description = term.get('Description', '').lower()
    category = term.get('category', '').lower()
    
    # تصنيف المصطلحات حسب النوع
    type_categories = {
        'tools': {
            'keywords': ['tool', 'equipment', 'device', 'machine', 'drill', 'jack', 'pump', 'wrench', 'screwdriver'],
            'terms': ['drill', 'wheel-jack', 'pump', 'wrench', 'screwdriver', 'hammer', 'pliers', 'saw']
        },
        'parts': {
            'keywords': ['engine', 'wheel', 'brake', 'gear', 'valve', 'pump', 'hose', 'pipe'],
            'terms': ['engine', 'wheel', 'brake', 'gear', 'valve', 'pump', 'hose', 'pipe']
        },
        'actions': {
            'keywords': ['lift', 'lower', 'turn', 'move', 'push', 'pull', 'adjust', 'repair'],
            'terms': ['lift-up', 'lower', 'turn', 'adjust', 'repair', 'maintain']
        },
        'safety': {
            'keywords': ['safety', 'warning', 'danger', 'emergency', 'protect', 'secure'],
            'terms': ['safety-glasses', 'warning-sign', 'emergency-stop', 'protective-gear']
        }
    }
    
    # تصنيف المصطلحات حسب التخصص
    specializations = {
        'mechanics': ['engine', 'mechanical', 'gear', 'pump', 'valve', 'piston', 'hydraulic'],
        'electricity': ['electric', 'current', 'voltage', 'circuit', 'wire', 'power'],
        'programming': ['code', 'program', 'software', 'development', 'algorithm'],
        'networking': ['network', 'protocol', 'router', 'switch', 'connection'],
        'hardware': ['computer', 'processor', 'memory', 'storage', 'device'],
        'security': ['security', 'protection', 'firewall', 'encryption', 'cyber']
    }
    
    # تحديد نوع المصطلح
    term_type = None
    max_type_score = 0
    
    for type_name, data in type_categories.items():
        keyword_score = sum(2 for kw in data['keywords'] if kw in english_term or kw in description)
        term_score = sum(3 for t in data['terms'] if t == english_term)
        total_score = keyword_score + term_score
        
        if total_score > max_type_score:
            max_type_score = total_score
            term_type = type_name
    
    # تحديد تخصص المصطلح
    specialization = None
    max_spec_score = 0
    
    # إذا كان التخصص محدد في المصطلح، استخدمه
    if category and category in specializations:
        specialization = category
    else:
        # وإلا، حاول تحديد التخصص من المصطلح والوصف
        for spec_name, keywords in specializations.items():
            score = sum(2 for kw in keywords if kw in english_term or kw in description)
            if score > max_spec_score:
                max_spec_score = score
                specialization = spec_name
    
    # قائمة المجلدات للبحث فيها
    search_paths = []
    
    # إضافة مجلد النوع إذا تم تحديده
    if term_type:
        search_paths.append(f'images/{term_type}')
    
    # إضافة مجلد التخصص إذا تم تحديده
    if specialization:
        search_paths.append(f'images/specializations/{specialization}')
    
    # إضافة المجلد الرئيسي
    search_paths.append('images')
    
    # محاولة العثور على الصورة
    for directory in search_paths:
        # تجربة أسماء مختلفة للملف
        file_variants = [
            english_term,
            english_term.replace(" ", "-"),
            english_term.replace(" ", "_")
        ]
        
        # تجربة امتدادات مختلفة
        for name in file_variants:
            for ext in ['.jpg', '.png', '.jpeg']:
                image_path = os.path.join(directory, name + ext)
                if os.path.exists(os.path.join(app.root_path, 'static', image_path)):
                    print(f"Found image for {english_term}: {image_path}")
                    return url_for('static', filename=image_path)
    
    print(f"No image found for term: {english_term} (type: {term_type}, specialization: {specialization})")
    return url_for('static', filename='images/placeholder.png')

def get_term_audio(term):
    """الحصول على مسار الصوت للمصطلح"""
    english_term = term.get('English Term', '')
    audio_path = f"{secure_filename(english_term)}.mp3"
    if not os.path.exists(os.path.join('static', 'audio', audio_path.lstrip('/'))):
        return None
    return url_for('static', filename=f'audio/{audio_path}')

@app.template_global()
def get_term_image_url(term):
    """دالة مساعدة للحصول على رابط الصورة في القوالب"""
    return get_term_image(term)

def get_tools_and_equipment():
    """الحصول على مصطلحات العدد والأدوات"""
    tools_keywords = ['tool', 'equipment', 'machine', 'device', 'wrench', 
                     'screwdriver', 'hammer', 'plier', 'saw', 'drill',
                     'gun', 'jack', 'pump', 'meter', 'gauge', 'tester',
                     'cutter', 'grinder', 'compressor', 'hoist',
                     'measure', 'tape', 'level', 'vise', 'clamp']
    
    tool_terms = []
    for term in terms:
        if not isinstance(term, dict):
            continue
        english_term = term['English Term'].lower()
        description = term.get('Description', '').lower()
        
        if any(keyword in english_term or keyword in description for keyword in tools_keywords):
            tool_terms.append(term)
    
    return tool_terms

def get_verbs():
    """الحصول على مصطلحات الأفعال التقنية"""
    verb_keywords = ['repair', 'fix', 'install', 'remove', 'adjust', 
                    'test', 'check', 'measure', 'connect', 'disconnect',
                    'maintain', 'service', 'operate', 'control', 'monitor',
                    'calibrate', 'diagnose', 'troubleshoot', 'inspect', 'verify',
                    'clean', 'replace', 'tighten', 'loosen', 'align',
                    'assemble', 'disassemble', 'weld', 'cut', 'drill']
    
    verb_terms = []
    for term in terms:
        if not isinstance(term, dict):
            continue
        english_term = term['English Term'].lower()
        description = term.get('Description', '').lower()
        
        if any(keyword in english_term or keyword in description for keyword in verb_keywords):
            verb_terms.append(term)
    
    return verb_terms

def get_specialized_terms(category):
    """الحصول على المصطلحات المتخصصة حسب الفئة"""
    categories_keywords = {
        'mechanics': ['mechanical', 'engine', 'gear', 'pump', 'valve', 'bearing', 'shaft', 'piston',
                     'transmission', 'brake', 'clutch', 'suspension', 'steering', 'exhaust'],
        'electricity': ['electrical', 'voltage', 'current', 'circuit', 'power', 'transformer', 'motor',
                       'battery', 'wire', 'relay', 'switch', 'fuse', 'conductor', 'insulator'],
        'electronics': ['electronic', 'circuit', 'component', 'semiconductor', 'transistor', 'resistor',
                       'capacitor', 'diode', 'sensor', 'microcontroller', 'processor', 'chip'],
        'programming': ['programming', 'code', 'software', 'algorithm', 'function', 'variable',
                       'database', 'interface', 'api', 'framework', 'library', 'debug'],
        'networks': ['network', 'protocol', 'router', 'switch', 'server', 'packet', 'bandwidth',
                    'ethernet', 'wifi', 'lan', 'wan', 'ip', 'dns', 'tcp'],
        'database': ['database', 'sql', 'query', 'table', 'record', 'field', 'key',
                    'index', 'join', 'transaction', 'backup', 'restore'],
        'security': ['security', 'cyber', 'encryption', 'firewall', 'authentication', 'threat',
                    'virus', 'malware', 'password', 'access', 'protection'],
        'web': ['web', 'html', 'css', 'javascript', 'http', 'browser', 'server',
                'client', 'frontend', 'backend', 'api', 'rest'],
        'mobile': ['mobile', 'app', 'android', 'ios', 'interface', 'touch',
                  'smartphone', 'tablet', 'gesture', 'notification'],
        'cloud': ['cloud', 'service', 'storage', 'virtualization', 'container', 'deployment',
                 'aws', 'azure', 'docker', 'kubernetes', 'scaling']
    }
    
    if category not in categories_keywords:
        return []
    
    keywords = categories_keywords[category]
    specialized_terms = []
    
    for term in terms:
        if not isinstance(term, dict):
            continue
        english_term = term['English Term'].lower()
        description = term.get('Description', '').lower()
        
        if any(keyword in english_term or keyword in description for keyword in keywords):
            specialized_terms.append(term)
    
    return specialized_terms

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/categories')
def categories():
    """صفحة التخصصات"""
    categories_list = {
        'mechanics': 'الميكانيكا',
        'electricity': 'الكهرباء',
        'electronics': 'الإلكترونيات',
        'programming': 'البرمجة',
        'networks': 'الشبكات',
        'database': 'قواعد البيانات',
        'security': 'الأمن السيبراني',
        'web': 'تطوير الويب',
        'mobile': 'تطوير الجوال',
        'cloud': 'الحوسبة السحابية'
    }
    return render_template('categories.html', categories=categories_list)

@app.route('/tools-equipment')
def tools_equipment():
    """صفحة العدد والأدوات"""
    tool_terms = get_tools_and_equipment()
    return render_template('terms_list.html', 
                         terms=tool_terms,
                         category="العدد والأدوات",
                         get_term_audio=get_term_audio,
                         get_term_image=get_term_image_url)

@app.route('/verbs')
def verbs():
    """صفحة الأفعال التقنية"""
    verb_terms = get_verbs()
    return render_template('terms_list.html', 
                         terms=verb_terms,
                         category="الأفعال التقنية",
                         get_term_audio=get_term_audio,
                         get_term_image=get_term_image_url)

@app.route('/games')
def games():
    """صفحة الألعاب التعليمية"""
    # اختيار 10 مصطلحات عشوائية للعبة
    game_terms = random.sample(terms, min(10, len(terms)))
    return render_template('games.html', terms=game_terms)

@app.route('/games/<game_type>')
def play_game(game_type):
    """تشغيل لعبة معينة"""
    if game_type in ['matching', 'memory', 'quiz']:
        # اختيار 10 مصطلحات عشوائية للعبة
        game_terms = random.sample(terms, min(10, len(terms)))
        return render_template(f'games/{game_type}.html', terms=game_terms)
    return redirect(url_for('games'))

@app.route('/games/category/<category>/<game_type>')
def play_category_game(category, game_type):
    """تشغيل لعبة لتخصص معين"""
    if game_type in ['matching', 'memory', 'quiz']:
        category_terms = get_specialized_terms(category)
        if category_terms:
            # اختيار 10 مصطلحات عشوائية من التخصص
            game_terms = random.sample(category_terms, min(10, len(category_terms)))
            return render_template(f'games/{game_type}.html', terms=game_terms)
    return redirect(url_for('games'))

@app.route('/specialized/<category>')
def specialized_terms(category):
    """عرض المصطلحات الخاصة بتخصص معين"""
    category_terms = get_specialized_terms(category)
    return render_template('terms_list.html', 
                         terms=category_terms,
                         category=category.title(),
                         get_term_audio=get_term_audio,
                         get_term_image=get_term_image_url)

@app.route('/terms')
def view_terms():
    """عرض قائمة المصطلحات"""
    return render_template('terms_list.html', 
                         terms=terms,
                         category="جميع المصطلحات",
                         get_term_audio=get_term_audio,
                         get_term_image=get_term_image_url)

@app.route('/add-term', methods=['POST'])
def add_term():
    """إضافة مصطلح جديد"""
    if request.method == 'POST':
        data = request.form
        
        # التحقق من وجود الصورة
        image = request.files.get('image')
        image_filename = ''
        
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_filename = filename
            
        new_term = {
            'English Term': data['english_term'],
            'Arabic Translation': data['arabic_term'],
            'Description': data['description'],
            'image_path': image_filename
        }
        
        # إضافة المصطلح الجديد
        terms.append(new_term)
        save_terms(terms)
        
        # توليد ملف الصوت للمصطلح الجديد
        audio_dir = os.path.join(app.root_path, 'static/audio')
        audio_filename = f"{secure_filename(new_term['English Term'])}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        if not os.path.exists(audio_path):
            tts = gTTS(text=new_term['English Term'], lang='en')
            tts.save(audio_path)
        
        return jsonify({'status': 'success', 'message': 'تمت إضافة المصطلح بنجاح'})
    
    return jsonify({'status': 'error', 'message': 'طريقة الطلب غير صحيحة'})

@app.route('/search')
def search():
    """البحث عن المصطلحات"""
    query = request.args.get('q', '').strip()
    results = []
    seen_terms = set()  # لمنع تكرار المصطلحات
    
    if query:
        query = query.lower()
        for term in terms:
            # تخطي المصطلح إذا كان مكرراً
            term_key = f"{term['English Term']}_{term['Arabic Translation']}"
            if term_key in seen_terms:
                continue
                
            # البحث في المصطلح الإنجليزي والعربي والوصف
            english_term = term['English Term'].lower()
            arabic_term = term['Arabic Translation'].lower()
            description = term.get('Description', '').lower()
            
            # البحث عن تطابق جزئي في أي من الحقول
            if (query in english_term or 
                english_term in query or
                query in arabic_term or 
                arabic_term in query or
                query in description):
                
                # محاولة العثور على الصورة المناسبة
                image_filename = f"{english_term.replace(' ', '-')}.png"
                if os.path.exists(os.path.join(app.root_path, 'static', 'images', image_filename)):
                    term['image_path'] = f'/static/images/{image_filename}'
                results.append(term)
                seen_terms.add(term_key)
    
    # ترتيب النتائج حسب الأهمية
    results.sort(key=lambda x: (
        query in x['English Term'].lower(),  # الأولوية للتطابق في المصطلح الإنجليزي
        query in x['Arabic Translation'].lower(),  # ثم التطابق في المصطلح العربي
        len(x['English Term'])  # المصطلحات الأقصر أولاً
    ), reverse=True)
    
    return render_template('search_results.html', 
                         query=query,
                         results=results,
                         get_term_audio=get_term_audio,
                         get_term_image=get_term_image_url)

@app.route('/audio/<filename>')
def serve_audio(filename):
    """تقديم ملفات الصوت"""
    return send_from_directory('static/audio', filename)

@app.route('/images/<filename>')
def serve_image(filename):
    """تقديم الصور"""
    return send_from_directory('static/images', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
