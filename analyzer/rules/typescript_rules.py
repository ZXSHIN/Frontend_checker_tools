"""TypeScript quality rules."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='TypeScript'):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': framework}


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_any_type(content))
    issues.extend(_check_as_any(content))
    issues.extend(_check_non_null_assertion(content))
    issues.extend(_check_implicit_any_params(content))
    issues.extend(_check_enum_usage(content))
    issues.extend(_check_missing_return_type(content))
    return issues


def _check_any_type(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r':\s*any\b', line) and 'any[]' not in line:
            issues.append(_issue(
                'ts-no-any', 'warning', 'Tipe any — Hilangkan Type Safety', i, s,
                f'Tipe any di baris {i}. Menghilangkan manfaat utama TypeScript.',
                'Ganti any dengan tipe yang spesifik. Gunakan unknown jika tipe tidak diketahui, lalu lakukan type narrowing dengan typeof/instanceof.'))
    return issues


def _check_as_any(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\bas\s+any\b', line):
            issues.append(_issue(
                'ts-as-any', 'warning', 'Type Assertion "as any" — Unsafe Cast', i, s,
                f'"as any" type assertion di baris {i}. Memaksa compiler mengabaikan type checking.',
                'Hindari "as any". Gunakan generic types, type guards, atau tipe yang benar. Jika terpaksa, tambahkan komentar // eslint-disable-next-line @typescript-eslint/no-explicit-any dengan penjelasan alasannya.'))
    return issues


def _check_non_null_assertion(content: str) -> List[Dict]:
    issues = []
    count = len(re.findall(r'\w+!\.|\w+!\[|\w+!\(', content))
    if count >= 3:
        for i, line in enumerate(content.split('\n'), 1):
            if re.search(r'\w+!\.|\w+!\[', line):
                issues.append(_issue(
                    'ts-non-null', 'info', f'Non-null Assertion (!) Berlebihan ({count}x)', i, line.strip(),
                    f'Non-null assertion operator (!) digunakan {count} kali. Bisa menyebabkan runtime error jika nilai ternyata null/undefined.',
                    'Gunakan optional chaining (?.) untuk akses aman: obj?.property. Atau lakukan null check eksplisit: if (value !== null) { ... }'))
                break
    return issues


def _check_implicit_any_params(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        # Detect function parameters without type annotations
        m = re.search(r'function\s+\w+\s*\(\s*(\w+)(?!\s*[?:,)])', line)
        if m and m.group(1) not in ('', 'void'):
            issues.append(_issue(
                'ts-implicit-any', 'warning', f'Parameter Fungsi Tanpa Type Annotation: {m.group(1)}', i, s,
                f'Parameter "{m.group(1)}" di baris {i} tidak memiliki type annotation — akan di-implicitly type sebagai any.',
                f'Tambahkan type annotation: function name({m.group(1)}: string) atau aktifkan "noImplicitAny": true di tsconfig.json.'))
    return issues


def _check_enum_usage(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\benum\s+\w+', line):
            issues.append(_issue(
                'ts-enum', 'info', 'Penggunaan enum — Pertimbangkan Alternatif', i, s,
                f'enum di baris {i}. TypeScript enums menghasilkan kode JavaScript tambahan dan memiliki beberapa kelemahan.',
                'Pertimbangkan menggunakan const object + as const: const Direction = { Up: "UP", Down: "DOWN" } as const; type Direction = typeof Direction[keyof typeof Direction];'))
    return issues


def _check_missing_return_type(content: str) -> List[Dict]:
    issues = []
    count = 0
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if count >= 2:
            break
        m = re.search(r'(?:export\s+)?(?:async\s+)?function\s+([A-Z]\w*)\s*\([^)]*\)\s*(?!\s*:)', line)
        if m and not re.search(r':\s*\w', line.split(')')[1] if ')' in line else ''):
            count += 1
            issues.append(_issue(
                'ts-return-type', 'info', f'Fungsi Tanpa Return Type: {m.group(1)}', i, s,
                f'Fungsi "{m.group(1)}" di baris {i} tidak memiliki explicit return type annotation.',
                'Tambahkan return type: function processData(input: string): ProcessedData { ... }. Meningkatkan dokumentasi dan deteksi bug.'))
    return issues
