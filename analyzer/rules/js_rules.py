"""JavaScript quality rules."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='JavaScript'):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': framework}


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_var(content))
    issues.extend(_check_loose_equality(content))
    issues.extend(_check_inner_html(content))
    issues.extend(_check_document_write(content))
    issues.extend(_check_async_without_try(content))
    issues.extend(_check_callback_hell(content))
    issues.extend(_check_for_in(content))
    issues.extend(_check_settimeout_no_clear(content))
    issues.extend(_check_magic_numbers(content))
    return issues


def _check_var(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\bvar\s+\w', line):
            issues.append(_issue(
                'no-var', 'warning', 'Penggunaan var (Gunakan const/let)', i, s,
                f'Keyword var ditemukan di baris {i}. var memiliki function scoping yang sering menyebabkan bug.',
                'Gunakan const untuk nilai yang tidak berubah, dan let untuk nilai yang berubah. Hindari var sepenuhnya.'))
    return issues


def _check_loose_equality(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'[^=!<>]={2}[^=]|[^=!<>]=={1}[^=]', line) and not re.search(r'={3}', line):
            if re.search(r'\b==\b|\b!=\b', line) and not re.search(r'===|!==', line):
                issues.append(_issue(
                    'eqeqeq', 'warning', 'Perbandingan Longgar (== / !=)', i, s,
                    f'Operator == atau != di baris {i}. Bisa menyebabkan bug karena type coercion.',
                    'Selalu gunakan === (strict equality) dan !== (strict inequality) untuk menghindari type coercion yang tidak terduga.'))
    return issues


def _check_inner_html(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\.innerHTML\s*=\s*(?![\'"]\s*[\'"]\s*;|[\'"]<\/?\w)', line):
            issues.append(_issue(
                'no-inner-html', 'error', 'innerHTML dengan Data Dinamis — XSS Risk', i, s,
                f'Mengassign innerHTML dengan data dinamis di baris {i}. Sangat berbahaya, rentan XSS attack.',
                'Gunakan textContent untuk teks biasa, atau DOMPurify.sanitize() jika harus menggunakan HTML. Pertimbangkan createElement() + appendChild().'))
    return issues


def _check_document_write(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'document\.write\s*\(', line):
            issues.append(_issue(
                'no-document-write', 'error', 'document.write() Deprecated', i, s,
                f'document.write() di baris {i}. Blocking, deprecated, dan dangerous. Jangan gunakan!',
                'Ganti dengan DOM manipulation API: document.createElement(), appendChild(), innerHTML dengan data yang di-sanitize.'))
    return issues


def _check_async_without_try(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\bawait\s+\w', line):
            block_start = max(0, i - 8)
            block = '\n'.join(lines[block_start:i])
            if 'try' not in block and 'catch' not in block:
                issues.append(_issue(
                    'async-no-try', 'warning', 'await Tanpa try/catch Error Handling', i, s,
                    f'await di baris {i} tidak terbungkus dalam try/catch. Jika gagal, error tidak tertangani.',
                    'Bungkus await dalam try/catch: try { const data = await fetch(...); } catch (error) { /* handle error */ }'))
    return issues


def _check_callback_hell(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if re.search(r'\.then\s*\(', line):
            # Count then chaining nearby
            block = '\n'.join(lines[i:min(i+15, len(lines))])
            then_count = len(re.findall(r'\.then\s*\(', block))
            if then_count >= 3:
                issues.append(_issue(
                    'callback-hell', 'warning', 'Promise Chaining Terlalu Panjang (Callback Hell)', i, line.strip(),
                    f'Ditemukan {then_count + 1} .then() berturut-turut mulai baris {i}. Sulit dibaca dan di-debug.',
                    'Gunakan async/await untuk kode yang lebih bersih dan mudah dibaca. Atau gunakan Promise.all() untuk concurrent operations.'))
    return issues


def _check_for_in(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\bfor\s*\(\s*\w+\s+in\s+\w', line):
            issues.append(_issue(
                'no-for-in', 'info', 'for...in Loop pada Array', i, s,
                f'for...in di baris {i} tidak aman untuk iterasi array karena bisa mengiterasi inherited properties.',
                'Untuk array gunakan for...of atau .forEach(). Untuk objek, gunakan Object.keys() / Object.entries() + for...of.'))
    return issues


def _check_settimeout_no_clear(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        m = re.search(r'\b(setTimeout|setInterval)\s*\(', line)
        if m and not re.search(r'(const|let|var)\s+\w+\s*=\s*' + m.group(1), line):
            if m.group(1) == 'setInterval':
                issues.append(_issue(
                    'interval-no-clear', 'warning', 'setInterval Tanpa Referensi untuk clearInterval', i, s,
                    f'setInterval() di baris {i} tidak disimpan ke variabel. Tidak bisa di-clear → memory leak risk.',
                    'Simpan ke variabel: const intervalId = setInterval(...); lalu clearInterval(intervalId) saat component unmount.'))
    return issues


def _check_magic_numbers(content: str) -> List[Dict]:
    issues = []
    skip_values = {'0', '1', '2', '100', '-1', '0.5', '360', '3600', '1000', '60'}
    count = 0
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*') or 'const ' in line or '=' in line[:line.find('=') - 1 if '=' in line else 0]:
            continue
        for m in re.finditer(r'\b(\d{3,})\b', line):
            if m.group(1) not in skip_values and count < 3:
                count += 1
                issues.append(_issue(
                    'magic-number', 'info', f'Magic Number: {m.group(1)}', i, s,
                    f'Angka literal {m.group(1)} di baris {i} tanpa nama yang jelas.',
                    f'Definisikan sebagai konstanta bernama: const MAX_RETRY_COUNT = {m.group(1)}; agar kode lebih mudah dipahami.'))
    return issues
