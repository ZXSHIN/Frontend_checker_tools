"""HTML-specific quality rules."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': 'HTML'}


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_doctype(content))
    issues.extend(_check_lang_attr(content))
    issues.extend(_check_title(content))
    issues.extend(_check_viewport(content))
    issues.extend(_check_meta_description(content))
    issues.extend(_check_img_alt(content))
    issues.extend(_check_blank_target(content))
    issues.extend(_check_empty_href(content))
    issues.extend(_check_deprecated_tags(content))
    issues.extend(_check_inline_styles(content))
    issues.extend(_check_form_labels(content))
    issues.extend(_check_script_in_head(content))
    issues.extend(_check_semantic_main(content))
    issues.extend(_check_empty_links(content))
    return issues


def _check_doctype(content: str) -> List[Dict]:
    if not re.search(r'<!DOCTYPE\s+html', content, re.IGNORECASE):
        return [_issue('html-doctype', 'error', 'DOCTYPE Tidak Ada', 1, content.split('\n')[0],
                       'File HTML tidak memiliki deklarasi <!DOCTYPE html>.',
                       'Tambahkan <!DOCTYPE html> sebagai baris pertama file HTML Anda.')]
    return []


def _check_lang_attr(content: str) -> List[Dict]:
    if re.search(r'<html\b', content, re.IGNORECASE) and not re.search(r'<html\b[^>]*\slang=', content, re.IGNORECASE):
        line = next((i+1 for i, l in enumerate(content.split('\n')) if '<html' in l.lower()), 1)
        return [_issue('html-lang', 'warning', 'Atribut lang Tidak Ada di <html>', line, f'<html>',
                       'Tag <html> tidak memiliki atribut lang. Penting untuk aksesibilitas dan SEO.',
                       'Tambahkan atribut lang: <html lang="id"> untuk Bahasa Indonesia atau <html lang="en"> untuk Inggris.')]
    return []


def _check_title(content: str) -> List[Dict]:
    if not re.search(r'<title\b[^>]*>[^<]+</title>', content, re.IGNORECASE):
        return [_issue('html-title', 'error', 'Tag <title> Tidak Ada atau Kosong', 1, '',
                       'Halaman tidak memiliki tag <title> atau tag-nya kosong. Wajib untuk SEO.',
                       'Tambahkan <title>Deskripsi Halaman Anda</title> di dalam <head>. Gunakan judul yang deskriptif (50-60 karakter).')]
    return []


def _check_viewport(content: str) -> List[Dict]:
    if not re.search(r'<meta\b[^>]*name=["\']viewport["\']', content, re.IGNORECASE):
        return [_issue('html-viewport', 'warning', 'Meta Viewport Tidak Ada', 1, '',
                       'Tidak ada meta viewport. Halaman tidak akan responsive di perangkat mobile.',
                       'Tambahkan di dalam <head>: <meta name="viewport" content="width=device-width, initial-scale=1.0">')]
    return []


def _check_meta_description(content: str) -> List[Dict]:
    if not re.search(r'<meta\b[^>]*name=["\']description["\']', content, re.IGNORECASE):
        return [_issue('html-meta-desc', 'warning', 'Meta Description Tidak Ada', 1, '',
                       'Tidak ada meta description. Ini sangat penting untuk SEO (tampil di hasil pencarian Google).',
                       'Tambahkan: <meta name="description" content="Deskripsi halaman Anda (150-160 karakter)">')]
    return []


def _check_img_alt(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        imgs = re.finditer(r'<img\b([^>]*?)/?>', line, re.IGNORECASE)
        for img in imgs:
            attrs = img.group(1)
            if 'alt=' not in attrs.lower():
                issues.append(_issue(
                    'img-alt', 'error', 'Atribut alt Tidak Ada pada <img>', i, line.strip(),
                    f'Tag <img> di baris {i} tidak memiliki atribut alt. Ini melanggar standar aksesibilitas (WCAG 2.1).',
                    'Tambahkan alt yang deskriptif: <img alt="Deskripsi gambar">. Untuk gambar dekoratif, gunakan alt="" (kosong).'))
            elif re.search(r'alt=["\']["\']', attrs) and 'role=' not in attrs.lower():
                pass  # empty alt on decorative image is OK
    return issues


def _check_blank_target(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        links = re.finditer(r'<a\b[^>]*target=["\']_blank["\'][^>]*>', line, re.IGNORECASE)
        for link in links:
            tag = link.group(0)
            if 'noopener' not in tag.lower():
                issues.append(_issue(
                    'link-noopener', 'error', 'target="_blank" Tanpa rel="noopener"', i, line.strip(),
                    f'Link dengan target="_blank" di baris {i} tidak memiliki rel="noopener noreferrer". Ini membuka celah tabnapping attack.',
                    'Tambahkan rel="noopener noreferrer": <a href="..." target="_blank" rel="noopener noreferrer">'))
    return issues


def _check_empty_href(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if re.search(r'<a\b[^>]*href=["\']#["\']', line, re.IGNORECASE):
            issues.append(_issue(
                'link-empty-href', 'warning', 'Link dengan href="#" Tanpa Handler', i, line.strip(),
                f'Link href="#" di baris {i} tidak memiliki tujuan yang jelas dan bisa menyebabkan jump ke atas halaman.',
                'Gunakan href="javascript:void(0)" atau tambahkan event handler onclick. Atau ganti dengan <button> jika memang bukan link navigasi.'))
    return issues


def _check_deprecated_tags(content: str) -> List[Dict]:
    issues = []
    deprecated = {
        'font': 'Gunakan CSS (font-family, font-size, color) sebagai gantinya.',
        'center': 'Gunakan CSS (text-align: center atau margin: auto) sebagai gantinya.',
        'marquee': 'Gunakan CSS animation atau JavaScript untuk efek scrolling text.',
        'blink': 'Tag ini tidak didukung di browser modern. Gunakan CSS animation.',
        'strike': 'Gunakan tag <s> atau <del> atau CSS text-decoration: line-through.',
        'frameset': 'Frameset sudah deprecated di HTML5. Gunakan layout CSS modern.',
        'frame': 'Gunakan <iframe> jika memang butuh, atau redesign layout dengan CSS.',
    }
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for tag, fix in deprecated.items():
            if re.search(rf'<{tag}\b', line, re.IGNORECASE):
                issues.append(_issue(
                    'deprecated-tag', 'warning', f'Tag HTML Deprecated: <{tag}>', i, line.strip(),
                    f'Tag <{tag}> sudah deprecated di HTML5 dan tidak sesuai standar modern.',
                    fix))
    return issues


def _check_inline_styles(content: str) -> List[Dict]:
    issues = []
    count = 0
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if re.search(r'\bstyle=["\'][^"\']+["\']', line, re.IGNORECASE):
            count += 1
            if count <= 3:  # Only report first 3 to avoid spam
                issues.append(_issue(
                    'no-inline-styles', 'info', 'Inline Style Ditemukan', i, line.strip(),
                    f'Inline style ditemukan di baris {i}. Sulit dimaintain dan override.',
                    'Pindahkan styling ke file CSS eksternal atau gunakan CSS class. Inline style memiliki specificity tinggi yang menyulitkan maintenance.'))
    return issues


def _check_form_labels(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if re.search(r'<input\b(?![^>]*type=["\'](?:hidden|submit|reset|button|checkbox|radio)["\'])[^>]*>', line, re.IGNORECASE):
            has_label = False
            # Check for aria-label or aria-labelledby
            if re.search(r'aria-label(?:ledby)?=', line, re.IGNORECASE):
                has_label = True
            # Check if id is present (might have corresponding label)
            if re.search(r'\bid=["\'][^"\']+["\']', line, re.IGNORECASE):
                has_label = True  # Assume label exists elsewhere
            if not has_label:
                issues.append(_issue(
                    'input-label', 'warning', 'Input Tanpa Label (Aksesibilitas)', i, line.strip(),
                    f'<input> di baris {i} mungkin tidak memiliki label yang berasosiasi. Melanggar standar aksesibilitas.',
                    'Tambahkan <label for="inputId"> atau atribut aria-label="Deskripsi" pada elemen input.'))
    return issues


def _check_script_in_head(content: str) -> List[Dict]:
    issues = []
    in_head = False
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if '<head' in line.lower():
            in_head = True
        if '</head' in line.lower():
            in_head = False
        if in_head and re.search(r'<script\b', line, re.IGNORECASE):
            if not re.search(r'defer|async', line, re.IGNORECASE):
                issues.append(_issue(
                    'script-in-head', 'warning', 'Script di <head> Tanpa defer/async', i, line.strip(),
                    f'<script> di <head> baris {i} tanpa defer atau async. Ini memblokir rendering halaman (render-blocking).',
                    'Tambahkan atribut defer: <script src="..." defer> atau pindahkan script ke sebelum </body>.'))
    return issues


def _check_semantic_main(content: str) -> List[Dict]:
    if re.search(r'<body', content, re.IGNORECASE) and not re.search(r'<main\b', content, re.IGNORECASE):
        return [_issue('semantic-main', 'info', 'Elemen Semantic <main> Tidak Ada', 1, '',
                       'Tidak ada elemen <main> di halaman. Penting untuk aksesibilitas dan screen reader.',
                       'Tambahkan <main> untuk membungkus konten utama halaman. Gunakan juga <header>, <nav>, <footer> untuk struktur semantic.')]
    return []


def _check_empty_links(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if re.search(r'<a\b[^>]*>\s*</a>', line, re.IGNORECASE):
            issues.append(_issue(
                'empty-link', 'warning', 'Link Kosong Tanpa Teks', i, line.strip(),
                f'Tag <a> kosong di baris {i}. Screen reader tidak bisa membaca link ini.',
                'Tambahkan teks atau aria-label pada link: <a href="..." aria-label="Deskripsi">atau tambahkan teks yang bermakna di dalam tag <a>.'))
    return issues
