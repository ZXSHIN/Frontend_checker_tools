"""
Main orchestrator: scans folder, dispatches rules, aggregates results.
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional

from .detector import detect_frameworks
from .rules import universal, html_rules, css_rules, js_rules
from .rules import react_rules, vue_rules, angular_rules
from .rules import typescript_rules, tailwind_rules

# ── Constants ─────────────────────────────────────────────────────────

SKIP_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', '.nuxt',
    'vendor', '__pycache__', '.venv', 'venv', 'coverage', '.cache',
    'out', '.turbo', '.vercel', '.netlify', 'storybook-static',
}

EXT_MAP = {
    '.html': 'html',
    '.htm':  'html',
    '.css':  'css',
    '.js':   'javascript',
    '.jsx':  'jsx',
    '.ts':   'typescript',
    '.tsx':  'tsx',
    '.vue':  'vue',
    '.svelte': 'svelte',
    '.scss': 'scss',
    '.sass': 'sass',
}

SEVERITY_WEIGHT = {'error': 10, 'warning': 3, 'info': 1}


# ── Public API ────────────────────────────────────────────────────────

def analyze_folder(folder_path: str) -> Dict:
    folder = Path(folder_path)

    # 1. Read package.json if available
    pkg = _read_json(folder / 'package.json')

    # 2. Collect files
    files = _collect_files(folder)
    if not files:
        return {
            'error': 'Tidak ada file frontend yang ditemukan. '
                     'Pastikan folder berisi file .html .css .js .jsx .ts .tsx .vue .svelte .scss',
            'files': [], 'frameworks': [], 'score': 0,
        }

    # 3. Read content
    all_content = ''
    for f in files:
        content = _safe_read(f['path'])
        f['content'] = content
        f['lines'] = content.count('\n') + 1
        all_content += content + '\n'

    # 4. Detect frameworks
    frameworks = detect_frameworks(all_content, pkg)
    fw_ids = {fw['id'] for fw in frameworks}

    # 5. Analyze each file
    file_results = []
    for f in files:
        result = _analyze_file(f, fw_ids)
        result['file'] = f['rel_path']
        result['type'] = f['type']
        result['lines'] = f['lines']
        file_results.append(result)

    # 6. Aggregate
    total_errors   = sum(r['errors']   for r in file_results)
    total_warnings = sum(r['warnings'] for r in file_results)
    total_info     = sum(r['info']     for r in file_results)
    total_passed   = sum(r['passed']   for r in file_results)

    score = _calc_project_score(total_errors, total_warnings, total_info, total_passed)
    grade = _score_to_grade(score)

    # 7. Flat issue list (with file reference)
    all_issues = []
    for r in file_results:
        for issue in r['issues']:
            all_issues.append({**issue, 'file': r['file']})

    # 8. Pre-deploy checklist
    checklist = _build_checklist(all_content, all_issues, fw_ids)

    return {
        'folder':        folder_path,
        'frameworks':    frameworks,
        'file_count':    len(file_results),
        'files':         file_results,
        'score':         score,
        'grade':         grade,
        'total_errors':  total_errors,
        'total_warnings':total_warnings,
        'total_info':    total_info,
        'total_passed':  total_passed,
        'deploy_ready':  total_errors == 0,
        'issues':        all_issues,
        'checklist':     checklist,
    }


# ── File collection ────────────────────────────────────────────────────

def _collect_files(folder: Path) -> List[Dict]:
    results = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for name in files:
            ext = Path(name).suffix.lower()
            if ext in EXT_MAP:
                path = Path(root) / name
                results.append({
                    'path':     str(path),
                    'rel_path': str(path.relative_to(folder)),
                    'type':     EXT_MAP[ext],
                    'name':     name,
                })
    return results


# ── Per-file analysis ─────────────────────────────────────────────────

def _analyze_file(f: Dict, fw_ids: set) -> Dict:
    content  = f['content']
    ftype    = f['type']
    filename = f['rel_path']
    issues: List[Dict] = []

    # Universal (JS-like files)
    if ftype in ('javascript', 'jsx', 'typescript', 'tsx', 'vue', 'svelte'):
        issues += universal.check_all(content, filename)

    # HTML also may contain inline JS
    if ftype == 'html':
        issues += html_rules.check_all(content, filename)
        if '<script' in content:
            issues += universal.check_all(content, filename)

    # CSS / SCSS
    if ftype in ('css',):
        issues += css_rules.check_css(content, filename)

    if ftype in ('scss', 'sass'):
        issues += css_rules.check_css(content, filename)
        issues += css_rules.check_scss(content, filename)

    # Plain JS
    if ftype in ('javascript', 'jsx'):
        issues += js_rules.check_all(content, filename)

    # TypeScript
    if ftype in ('typescript', 'tsx'):
        issues += js_rules.check_all(content, filename)
        issues += typescript_rules.check_all(content, filename)

    # React
    if 'react' in fw_ids and ftype in ('javascript', 'jsx', 'typescript', 'tsx'):
        issues += react_rules.check_all(content, filename)

    # Next.js
    if 'nextjs' in fw_ids and ftype in ('javascript', 'jsx', 'typescript', 'tsx'):
        issues += react_rules.check_nextjs(content, filename)

    # Vue
    if ftype == 'vue':
        issues += js_rules.check_all(content, filename)
        issues += vue_rules.check_all(content, filename)
        if 'typescript' in fw_ids:
            issues += typescript_rules.check_all(content, filename)

    # Angular
    if 'angular' in fw_ids and ftype in ('typescript', 'tsx'):
        issues += angular_rules.check_all(content, filename)

    # Tailwind
    if 'tailwind' in fw_ids and ftype in ('html', 'jsx', 'tsx', 'vue', 'svelte'):
        issues += tailwind_rules.check_all(content, filename)

    # Deduplicate
    issues = _dedup(issues)

    errors   = sum(1 for i in issues if i['severity'] == 'error')
    warnings = sum(1 for i in issues if i['severity'] == 'warning')
    info_cnt = sum(1 for i in issues if i['severity'] == 'info')
    passed   = max(0, _estimate_passed(ftype, fw_ids) - errors - warnings)
    score    = max(0, 100 - errors * 10 - warnings * 4 - info_cnt)

    return {
        'issues':   issues,
        'errors':   errors,
        'warnings': warnings,
        'info':     info_cnt,
        'passed':   passed,
        'score':    min(100, score),
    }


def _estimate_passed(ftype: str, fw_ids: set) -> int:
    base = {'html': 14, 'css': 10, 'scss': 8, 'sass': 8,
            'javascript': 9, 'jsx': 11, 'typescript': 10,
            'tsx': 12, 'vue': 11, 'svelte': 8}
    return base.get(ftype, 8) + (3 if 'typescript' in fw_ids else 0)


# ── Scoring ───────────────────────────────────────────────────────────

def _calc_project_score(errors: int, warnings: int, info: int, passed: int) -> int:
    total = errors + warnings + info + passed
    if total == 0:
        return 100
    raw = int(((passed + info * 0.5 + warnings * 0.25) / total) * 100)
    penalty = errors * 5 + warnings * 1
    return max(0, min(100, raw - penalty))


def _score_to_grade(score: int) -> str:
    if score >= 90: return 'A'
    if score >= 80: return 'B'
    if score >= 70: return 'C'
    if score >= 60: return 'D'
    return 'F'


# ── Pre-deploy checklist ──────────────────────────────────────────────

def _build_checklist(content: str, issues: List[Dict], fw_ids: set) -> List[Dict]:
    def has_rule(rule_id: str) -> bool:
        return any(i['rule'] == rule_id for i in issues)

    def _item(text: str, passed: bool, detail: str = '') -> Dict:
        return {'text': text, 'passed': passed, 'detail': detail}

    items = [
        _item('Tidak ada console.log tersisa',
              not has_rule('no-console'), 'Hapus semua console statements'),
        _item('Tidak ada debugger statement',
              not has_rule('no-debugger'), 'Hapus semua debugger'),
        _item('Tidak ada eval() (security)',
              not has_rule('no-eval'), 'Ganti eval() dengan alternatif yang aman'),
        _item('Tidak ada hardcoded secrets/API keys',
              not has_rule('no-hardcoded-secrets'), 'Pindahkan ke environment variables'),
        _item('Semua TODO/FIXME/HACK diselesaikan',
              not has_rule('no-todo-in-prod'), 'Selesaikan atau catat di issue tracker'),
    ]

    if re.search(r'<!DOCTYPE|<html', content, re.IGNORECASE):
        items += [
            _item('<!DOCTYPE html> ada',              not has_rule('html-doctype')),
            _item('Meta viewport ada (responsive)',   not has_rule('html-viewport')),
            _item('Meta description ada (SEO)',       not has_rule('html-meta-desc')),
            _item('Semua <img> punya atribut alt',   not has_rule('img-alt')),
            _item('Link _blank pakai rel=noopener',  not has_rule('link-noopener')),
        ]

    if 'vue' in fw_ids:
        items += [
            _item('Semua v-for punya :key unik',        not has_rule('vue-vfor-key')),
            _item('Tidak ada v-if + v-for di elemen sama', not has_rule('vue-vfor-vif')),
            _item('Tidak ada mutasi langsung pada props', not has_rule('vue-prop-mutation')),
            _item('Tidak ada v-html tanpa sanitasi (XSS)', not has_rule('vue-vhtml')),
        ]

    if 'react' in fw_ids or 'nextjs' in fw_ids:
        items += [
            _item('Semua list item punya key prop',     not has_rule('missing-key')),
            _item('Hooks tidak dipanggil dalam kondisi', not has_rule('hook-in-condition')),
            _item('Tidak ada class= (harus className=)', not has_rule('class-classname')),
        ]
        if 'nextjs' in fw_ids:
            items += [
                _item('Gunakan next/image (bukan <img>)',   not has_rule('nextjs-img')),
                _item('Gunakan next/link untuk internal link', not has_rule('nextjs-link')),
            ]

    if 'typescript' in fw_ids:
        items += [
            _item('Tidak ada penggunaan tipe any', not has_rule('ts-no-any') and not has_rule('angular-any')),
            _item('Tidak ada unsafe "as any" cast', not has_rule('ts-as-any')),
        ]

    if 'angular' in fw_ids:
        items += [
            _item('Observable selalu di-unsubscribe', not has_rule('angular-subscribe')),
        ]

    if re.search(r'\{.*@media', content):
        items.append(_item('CSS memiliki media queries (responsive)', True))
    elif re.search(r'\.css|\.scss', content):
        items.append(_item('CSS memiliki media queries (responsive)',
                           not has_rule('no-media-query')))

    return items


# ── Utilities ─────────────────────────────────────────────────────────

def _dedup(issues: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for issue in issues:
        key = (issue.get('rule', ''), issue.get('line', 0),
               issue.get('message', '')[:40])
        if key not in seen:
            seen.add(key)
            out.append(issue)
    return out


def _safe_read(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ''


def _read_json(path: Path) -> Optional[Dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None
