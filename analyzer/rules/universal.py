"""Universal rules - apply to all JS/TS/JSX/TSX/Vue/Svelte files."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='Universal'):
    return {
        'rule': rule,
        'severity': severity,
        'name': name,
        'line': line,
        'snippet': (snippet or '').strip()[:120],
        'message': message,
        'fix': fix,
        'framework': framework,
    }


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_console(content))
    issues.extend(_check_debugger(content))
    issues.extend(_check_eval(content))
    issues.extend(_check_alert(content))
    issues.extend(_check_hardcoded_secrets(content))
    issues.extend(_check_todos(content))
    issues.extend(_check_commented_blocks(content))
    return issues


# ── Individual checks ─────────────────────────────────────────────────

def _check_console(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*') or s.startswith('#'):
            continue
        m = re.search(r'\bconsole\.(log|warn|error|info|debug|table|dir|group|groupEnd|time|timeEnd)\s*\(', line)
        if m:
            issues.append(_issue(
                'no-console', 'error', 'Console Statement Tertinggal', i, s,
                f'console.{m.group(1)}() ditemukan — harus dihapus sebelum produksi.',
                'Hapus semua console statements. Gunakan conditional logging: if (process.env.NODE_ENV !== "production") console.log(...)'))
    return issues


def _check_debugger(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\bdebugger\b', line):
            issues.append(_issue(
                'no-debugger', 'error', 'Debugger Statement', i, s,
                f'Keyword debugger ditemukan di baris {i}. Akan menghentikan eksekusi di browser DevTools.',
                'Hapus semua statement debugger sebelum deploy ke produksi.'))
    return issues


def _check_eval(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\beval\s*\(', line):
            issues.append(_issue(
                'no-eval', 'error', 'Penggunaan eval() — Security Risk', i, s,
                f'eval() ditemukan di baris {i}. Membuka celah XSS dan sangat berbahaya.',
                'Ganti eval() dengan JSON.parse() untuk data JSON, atau refactor logika agar tidak perlu dynamic code execution.'))
    return issues


def _check_alert(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        m = re.search(r'\b(alert|confirm|prompt)\s*\(', line)
        if m:
            issues.append(_issue(
                'no-browser-dialog', 'warning', f'{m.group(1)}() di Kode Produksi', i, s,
                f'{m.group(1)}() ditemukan di baris {i}. Tidak sesuai untuk antarmuka produksi.',
                'Ganti dengan UI dialog/modal yang proper. Gunakan library seperti SweetAlert2 atau komponen modal dari framework UI Anda.'))
    return issues


def _check_hardcoded_secrets(content: str) -> List[Dict]:
    issues = []
    patterns = [
        (r'(?:api[_-]?key|apiKey|API_KEY)\s*[=:]\s*["\'][A-Za-z0-9_\-]{8,}["\']', 'API Key'),
        (r'(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{3,}["\']', 'Password'),
        (r'(?:secret[_-]?key|secretKey|SECRET)\s*[=:]\s*["\'][A-Za-z0-9_\-]{8,}["\']', 'Secret Key'),
        (r'(?:access[_-]?token|accessToken|ACCESS_TOKEN)\s*[=:]\s*["\'][A-Za-z0-9_\-\.]{10,}["\']', 'Access Token'),
        (r'(?:private[_-]?key|privateKey|PRIVATE_KEY)\s*[=:]\s*["\'][^"\']{10,}["\']', 'Private Key'),
        (r'(?:auth[_-]?token|authToken)\s*[=:]\s*["\'][A-Za-z0-9_\-\.]{10,}["\']', 'Auth Token'),
    ]
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*') or 'process.env' in line or 'import.meta.env' in line:
            continue
        for pattern, secret_type in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(_issue(
                    'no-hardcoded-secrets', 'error', f'Hardcoded {secret_type} Terdeteksi', i, s,
                    f'{secret_type} di-hardcode di baris {i}. KRITIS — jangan pernah commit ini ke repository!',
                    f'Pindahkan ke file .env dan akses via process.env.VAR_NAME atau import.meta.env.VITE_VAR_NAME. Tambahkan .env ke .gitignore.'))
                break
    return issues


def _check_todos(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        m = re.search(r'(?://|/\*|<!--\s*|#)\s*(TODO|FIXME|HACK|XXX|BUG)\b[:\s]*(.*)', line, re.IGNORECASE)
        if m:
            tag = m.group(1).upper()
            text = m.group(2).strip()[:60]
            issues.append(_issue(
                'no-todo-in-prod', 'info', f'{tag} Comment Belum Diselesaikan', i, line.strip(),
                f'{tag}: {text}' if text else f'{tag} ditemukan di baris {i} — belum diselesaikan.',
                'Selesaikan semua TODO/FIXME/HACK sebelum deploy ke produksi. Catat di issue tracker jika perlu ditunda.'))
    return issues


def _check_commented_blocks(content: str) -> List[Dict]:
    """Detect large blocks of commented-out code."""
    issues = []
    lines = content.split('\n')
    consecutive = 0
    start_line = 0
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith('//') and len(s) > 3:
            if consecutive == 0:
                start_line = i
            consecutive += 1
        else:
            if consecutive >= 5:
                issues.append(_issue(
                    'no-commented-code', 'info', 'Blok Kode Di-comment (Dead Code)', start_line, lines[start_line - 1].strip(),
                    f'{consecutive} baris kode berturut-turut di-comment dimulai dari baris {start_line}.',
                    'Hapus kode yang sudah tidak dipakai. Gunakan version control (git) untuk menyimpan riwayat kode lama.'))
            consecutive = 0
    return issues
