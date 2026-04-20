"""Tailwind CSS quality rules."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='Tailwind CSS'):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': framework}


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_class_overload(content))
    issues.extend(_check_arbitrary_values(content))
    issues.extend(_check_inline_style_with_tailwind(content))
    issues.extend(_check_responsive_inconsistency(content))
    return issues


def _check_class_overload(content: str) -> List[Dict]:
    issues = []
    threshold = 15
    for i, line in enumerate(content.split('\n'), 1):
        m = re.search(r'class(?:Name)?=["\'](.*?)["\']', line)
        if m:
            classes = m.group(1).split()
            if len(classes) > threshold:
                issues.append(_issue(
                    'tailwind-class-overload', 'warning', f'Terlalu Banyak Utility Class ({len(classes)} class)', i, line.strip(),
                    f'{len(classes)} utility class Tailwind pada satu elemen di baris {i}. Sulit dibaca dan dimaintain.',
                    f'Ekstrak ke komponen reusable atau gunakan @apply di CSS: .btn-primary {{ @apply bg-blue-500 text-white px-4 py-2 rounded; }}'))
    return issues


def _check_arbitrary_values(content: str) -> List[Dict]:
    issues = []
    count = 0
    for i, line in enumerate(content.split('\n'), 1):
        matches = re.findall(r'\w+\[[\w#%\.]+\]', line)
        if matches and count < 3:
            count += len(matches)
            issues.append(_issue(
                'tailwind-arbitrary', 'info', f'Arbitrary Value Tailwind: {", ".join(matches[:3])}', i, line.strip(),
                f'Arbitrary values {matches} di baris {i}. Hardcoded values yang tidak mengikuti design system.',
                'Definisikan nilai custom di tailwind.config.js: theme: { extend: { colors: { brand: "#1a1a2e" } } } dan gunakan class yang proper.'))
    return issues


def _check_inline_style_with_tailwind(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        has_class = re.search(r'class(?:Name)?=["\']', line)
        has_inline = re.search(r'style=["\']', line)
        if has_class and has_inline:
            issues.append(_issue(
                'tailwind-inline-mix', 'warning', 'Mixing Tailwind dengan Inline Style', i, line.strip(),
                f'Elemen di baris {i} menggunakan Tailwind class DAN inline style sekaligus. Tidak konsisten.',
                'Pilih satu pendekatan: gunakan Tailwind class saja, atau gunakan CSS custom saja. Mixing keduanya menyulitkan maintenance.'))
    return issues


def _check_responsive_inconsistency(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        m = re.search(r'class(?:Name)?=["\'](.*?)["\']', line)
        if m:
            classes = m.group(1)
            has_md = 'md:' in classes
            has_lg = 'lg:' in classes
            has_sm = 'sm:' in classes
            if (has_md or has_lg) and not has_sm:
                issues.append(_issue(
                    'tailwind-responsive', 'info', 'Responsive Class Tidak Lengkap (Mobile-First)', i, line.strip(),
                    f'Menggunakan md:/lg: tapi tidak ada sm: di baris {i}. Mungkin tampilan mobile terabaikan.',
                    'Tailwind menggunakan mobile-first approach. Pastikan tampilan mobile (default, tanpa prefix) sudah benar, lalu tambahkan sm:, md:, lg: untuk ukuran lebih besar.'))
    return issues
