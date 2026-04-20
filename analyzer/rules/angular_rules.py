"""Angular quality rules."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='Angular'):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': framework}


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_subscription_unsubscribe(content))
    issues.extend(_check_template_function_call(content))
    issues.extend(_check_change_detection(content))
    issues.extend(_check_any_type(content))
    issues.extend(_check_direct_dom(content))
    issues.extend(_check_empty_catch(content))
    return issues


def _check_subscription_unsubscribe(content: str) -> List[Dict]:
    issues = []
    if re.search(r'\.subscribe\s*\(', content):
        has_unsubscribe = bool(re.search(r'\.unsubscribe\s*\(|takeUntil|takeUntilDestroyed|async\s+pipe', content))
        if not has_unsubscribe:
            line = next((i+1 for i, l in enumerate(content.split('\n')) if '.subscribe(' in l), 1)
            issues.append(_issue(
                'angular-subscribe', 'warning', 'Observable Subscribe Tanpa Unsubscribe — Memory Leak', line,
                '.subscribe()',
                'Observable di-subscribe tapi tidak ada unsubscribe(), takeUntil(), atau async pipe. Ini menyebabkan memory leak.',
                'Gunakan takeUntilDestroyed(): .subscribe().pipe(takeUntilDestroyed(this.destroyRef)). Atau gunakan async pipe di template. Atau manually unsubscribe di ngOnDestroy.'))
    return issues


def _check_template_function_call(content: str) -> List[Dict]:
    issues = []
    # Detect function calls in HTML template sections
    in_template = False
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if '@Component' in line or 'templateUrl' in line:
            break
        if 'template:' in line or '<template>' in line:
            in_template = True
        if re.search(r'\{\{\s*\w+\s*\(', line) and in_template:
            issues.append(_issue(
                'angular-template-fn', 'warning', 'Function Call di Template — Performa Buruk', i, line.strip(),
                f'Memanggil function langsung di template baris {i}. Dipanggil setiap change detection cycle.',
                'Gunakan Pipe (pure) atau simpan hasil ke property/getter. Atau gunakan OnPush change detection untuk mengurangi cycles.'))
    return issues


def _check_change_detection(content: str) -> List[Dict]:
    if '@Component' in content and 'changeDetection' not in content:
        return [_issue(
            'angular-onpush', 'info', 'Tidak Menggunakan OnPush Change Detection', 1, '@Component()',
            'Komponen tidak menggunakan ChangeDetectionStrategy.OnPush. Default strategy tidak efisien untuk aplikasi besar.',
            'Tambahkan ke @Component: changeDetection: ChangeDetectionStrategy.OnPush. Ini meningkatkan performa signifikan.')]
    return []


def _check_any_type(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r':\s*any\b', line) or re.search(r'<any>', line):
            issues.append(_issue(
                'angular-any', 'warning', 'Penggunaan Tipe any — TypeScript Antipattern', i, s,
                f'Tipe any di baris {i}. Menghilangkan manfaat TypeScript dan bisa menyembunyikan bug.',
                'Ganti any dengan tipe yang spesifik. Jika tidak tahu tipenya, gunakan unknown dan lakukan type narrowing.'))
    return issues


def _check_direct_dom(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'document\.querySelector|document\.getElementById|document\.getElementsBy', line):
            issues.append(_issue(
                'angular-direct-dom', 'warning', 'Direct DOM Manipulation di Angular', i, s,
                f'Direct DOM manipulation di baris {i}. Tidak idiomatik di Angular dan bisa konflik dengan change detection.',
                'Gunakan @ViewChild() dengan ElementRef, atau Renderer2 untuk DOM manipulation yang aman dan cross-platform.'))
    return issues


def _check_empty_catch(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if re.search(r'\}\s*catch\s*\([^)]*\)\s*\{', line):
            next_lines = '\n'.join(lines[i:min(i+3, len(lines))])
            if re.search(r'^\s*\}\s*$', next_lines.split('\n')[0] if next_lines else ''):
                issues.append(_issue(
                    'empty-catch', 'warning', 'Empty Catch Block — Error Ditelan', i, line.strip(),
                    f'Catch block kosong di baris {i}. Error dibiarkan begitu saja tanpa penanganan.',
                    'Selalu handle error di catch block: setidaknya log ke monitoring system atau tampilkan pesan ke user.'))
    return issues
