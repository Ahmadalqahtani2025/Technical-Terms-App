import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, unquote

def ensure_dir(directory):
    """التأكد من وجود المجلد"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_image(url, save_path):
    """تنزيل الصورة من الرابط وحفظها في المسار المحدد"""
    headers = {
        'User-Agent': 'TechnicalTermsApp/1.0 (https://github.com/yourusername/technical-terms-app; your@email.com) Python/3.9'
    }
    try:
        print(f"محاولة تنزيل الصورة من: {url}")
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"تم تنزيل: {save_path}")
        return True
    except Exception as e:
        print(f"خطأ في تنزيل {url}: {str(e)}")
        return False

def get_original_image_url(wikimedia_url):
    """الحصول على رابط الصورة الأصلية من صفحة ويكيميديا"""
    headers = {
        'User-Agent': 'TechnicalTermsApp/1.0 (https://github.com/yourusername/technical-terms-app; your@email.com) Python/3.9'
    }
    try:
        print(f"جاري تحليل صفحة: {wikimedia_url}")
        response = requests.get(wikimedia_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # محاولة العثور على رابط التنزيل المباشر
        download_link = soup.find('a', {'download': True})
        if download_link and 'href' in download_link.attrs:
            return urljoin('https://commons.wikimedia.org', download_link['href'])
        
        # محاولة العثور على الصورة الأصلية
        original_file = soup.find('div', {'class': 'fullImageLink'})
        if original_file:
            img = original_file.find('img')
            if img and 'src' in img.attrs:
                return urljoin('https://commons.wikimedia.org', img['src'])
        
        # محاولة العثور على أي صورة في الصفحة
        img_element = soup.find('img', {'class': 'mw-file-element'})
        if img_element and 'src' in img_element.attrs:
            return urljoin('https://commons.wikimedia.org', img_element['src'])
            
        return None
    except Exception as e:
        print(f"خطأ في تحليل {wikimedia_url}: {str(e)}")
        return None

def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المسموح بها"""
    # إزالة الأحرف غير المسموح بها في أسماء الملفات
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # إزالة الأقواس والمسافات الزائدة
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename

def main():
    # قراءة ملف الروابط
    with open('image_links.txt', 'r', encoding='utf-8') as file:
        content = file.read()

    # تحديد المجلد الحالي كمجلد static/images
    base_dir = os.path.join('static', 'images')
    
    # البحث عن الروابط والمجلدات
    current_dir = None
    for line in content.split('\n'):
        if line.startswith('##'):
            # استخراج اسم المجلد من العنوان
            dir_match = re.search(r'\((.*?)\)', line)
            if dir_match:
                current_dir = dir_match.group(1)
                ensure_dir(os.path.join(base_dir, current_dir))
                print(f"\nالعمل على المجلد: {current_dir}")
        elif line.startswith('###'):
            # التعامل مع المجلدات الفرعية في specializations
            subdir_match = re.search(r'\((.*?)\)', line)
            if subdir_match:
                current_dir = os.path.join('specializations', subdir_match.group(1))
                ensure_dir(os.path.join(base_dir, current_dir))
                print(f"\nالعمل على المجلد: {current_dir}")
        elif 'commons.wikimedia.org' in line:
            # استخراج الرابط
            url_match = re.search(r'https://commons\.wikimedia\.org/wiki/File:[^)\s]+', line)
            if url_match and current_dir:
                wikimedia_url = url_match.group(0)
                
                # استخراج اسم الملف من الرابط
                filename = wikimedia_url.split('File:')[-1]
                filename = unquote(filename)  # فك ترميز URL
                filename = clean_filename(filename)
                
                # الحصول على رابط الصورة الأصلية
                original_url = get_original_image_url(wikimedia_url)
                if original_url:
                    # تنزيل الصورة
                    save_path = os.path.join(base_dir, current_dir, filename)
                    download_image(original_url, save_path)

if __name__ == '__main__':
    main()
