"""CSS and SCSS/SASS quality rules."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='CSS'):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': framework}


def check_css(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_important(content))
    issues.extend(_check_no_media_query(content, filename))
    issues.extend(_check_high_z_index(content))
    issues.extend(_check_duplicate_selectors(content))
    issues.extend(_check_empty_rules(content))
    issues.extend(_check_star_selector(content))
    issues.extend(_check_magic_colors(content))
    issues.extend(_check_fixed_width_no_max(content))
    return issues


def check_scss(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_scss_nesting_depth(content))
    issues.extend(_check_scss_extend(content))
    issues.extend(_check_important(content))
    return issues


# ── CSS Checks ─────────────────────────────────────────────────────────

def _check_important(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('/*') or s.startswith('*') or s.startswith('//'):
            continue
        if re.search(r'!\s*important\b', line):
            issues.append(_issue(
                'no-important', 'warning', 'Penggunaan !important', i, s,
                f'!important ditemukan di baris {i}. Menyebabkan specificity wars dan sulitnya maintenance.',
                'Redesign CSS selector agar lebih spesifik alih-alih menggunakan !important. Ini tanda ada masalah specificity.'))
    return issues


def _check_no_media_query(content: str, filename: str) -> List[Dict]:
    lines = content.split('\n')
    if len(lines) > 30 and not re.search(r'@media\s', content):
        return [_issue(
            'no-media-query', 'warning', 'Tidak Ada Media Query (Responsive)', 1, '',
            f'File CSS ini ({len(lines)} baris) tidak memiliki @media query. Kemungkinan besar tidak responsive.',
            'Tambahkan media queries untuk breakpoint umum: @media (max-width: 768px) { ... } dan @media (max-width: 480px) { ... }')]
    return []


def _check_high_z_index(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        m = re.search(r'z-index\s*:\s*(\d+)', line)
        if m and int(m.group(1)) >= 9999:
            issues.append(_issue(
                'high-z-index', 'info', 'Magic z-index Terlalu Tinggi', i, line.strip(),
                f'z-index: {m.group(1)} ditemukan. Magic number yang sangat tinggi menandakan masalah stacking context.',
                'Gunakan sistem z-index yang terstruktur (misal: 10, 20, 30, ...). Definisikan sebagai CSS variable: --z-modal: 100; --z-tooltip: 200;'))
    return issues


def _check_duplicate_selectors(content: str) -> List[Dict]:
    issues = []
    selectors = {}
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s and not s.startswith('/*') and not s.startswith('*') and not s.startswith('@') and s.endswith('{'):
            selector = s.rstrip('{').strip()
            if len(selector) > 1:
                if selector in selectors:
                    issues.append(_issue(
                        'duplicate-selector', 'warning', 'Selector CSS Duplikat', i, s,
                        f'Selector "{selector}" sudah ada di baris {selectors[selector]}. Duplikasi yang tidak perlu.',
                        'Gabungkan rules dengan selector yang sama. Ini tanda ada masalah organisasi CSS.'))
                else:
                    selectors[selector] = i
    return issues


def _check_empty_rules(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if re.search(r'[^@\s][^{]*\{\s*\}', s) or (s.endswith('{') and i < len(lines) and lines[i].strip() == '}'):
            issues.append(_issue(
                'empty-rule', 'info', 'CSS Rule Kosong', i, s,
                f'Rule CSS kosong ditemukan di baris {i}. Dead code.',
                'Hapus rule CSS yang kosong. Ini adalah dead code yang tidak berguna.'))
    return issues


def _check_star_selector(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if re.search(r'(?:^|\s)\*\s*\{', line.strip()):
            issues.append(_issue(
                'star-selector', 'warning', 'Universal Selector (*) Berlebihan', i, line.strip(),
                f'Universal selector (*) ditemukan di baris {i}. Berdampak besar pada performa rendering.',
                'Hindari * { } untuk styling umum. Gunakan CSS reset yang lebih spesifik atau targeted selectors.'))
    return issues


def _check_magic_colors(content: str) -> List[Dict]:
    issues = []
    magic_colors = {'red', 'blue', 'green', 'yellow', 'black', 'white', 'purple', 'orange', 'pink'}
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('/*') or s.startswith('*'):
            continue
        m = re.search(r'(?:color|background|border-color|outline-color)\s*:\s*(\w+)\b', line)
        if m and m.group(1).lower() in magic_colors:
            issues.append(_issue(
                'magic-color', 'info', f'Warna Hardcoded: {m.group(1)}', i, s,
                f'Warna "{m.group(1)}" di-hardcode di baris {i}. Tidak konsisten dengan design system.',
                'Gunakan CSS Custom Properties (variables): --color-primary: #6366f1; dan pakai via var(--color-primary).'))
    return issues


def _check_fixed_width_no_max(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        m = re.search(r'width\s*:\s*(\d+)px', line)
        if m and int(m.group(1)) > 400:
            block_start = max(0, i - 5)
            block = '\n'.join(content.split('\n')[block_start:i + 3])
            if 'max-width' not in block:
                issues.append(_issue(
                    'fixed-width', 'info', 'Lebar Tetap Tanpa max-width', i, line.strip(),
                    f'width: {m.group(1)}px ditemukan tanpa max-width. Mungkin tidak responsive di layar kecil.',
                    'Pertimbangkan mengganti dengan max-width atau menggunakan width: 100% dengan max-width tertentu.'))
    return issues


# ── SCSS Checks ────────────────────────────────────────────────────────

def _check_scss_nesting_depth(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    depth = 0
    for i, line in enumerate(lines, 1):
        depth += line.count('{') - line.count('}')
        if depth > 4:
            issues.append(_issue(
                'scss-nesting', 'warning', f'SCSS Nesting Terlalu Dalam (Level {depth})', i, line.strip(),
                f'Nesting CSS {depth} level dalam di baris {i}. Menghasilkan selector yang sangat spesifik dan sulit di-override.',
                'Batasi nesting maksimal 3-4 level. Pertimbangkan menggunakan BEM naming convention alih-alih nesting dalam.',
                'SCSS'))
    return issues


def _check_scss_extend(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if re.search(r'@extend\s+', line):
            issues.append(_issue(
                'scss-extend', 'info', '@extend Dapat Menyebabkan CSS Bloat', i, line.strip(),
                f'@extend ditemukan di baris {i}. Bisa menghasilkan output CSS yang besar dan tidak terduga.',
                'Gunakan @mixin + @include sebagai alternatif @extend yang lebih aman dan terprediksi.',
                'SCSS'))
    return issues
