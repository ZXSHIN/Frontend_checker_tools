"""React and Next.js quality rules."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='React'):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': framework}


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_component_naming(content, filename))
    issues.extend(_check_key_index(content))
    issues.extend(_check_missing_key(content))
    issues.extend(_check_hooks_in_condition(content))
    issues.extend(_check_dom_manipulation(content))
    issues.extend(_check_class_vs_classname(content))
    issues.extend(_check_for_vs_htmlfor(content))
    issues.extend(_check_useeffect_no_deps(content))
    issues.extend(_check_missing_prop_types(content))
    return issues


def check_nextjs(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_nextjs_img(content))
    issues.extend(_check_nextjs_link(content))
    issues.extend(_check_nextjs_secrets(content))
    issues.extend(_check_use_client_overuse(content))
    return issues


# ── React Checks ────────────────────────────────────────────────────────

def _check_component_naming(content: str, filename: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        m = re.search(r'(?:function|const)\s+([a-z]\w*)\s*(?:=\s*(?:\([^)]*\)|React\.memo|\(\s*\))\s*=>|(?:\([^)]*\))\s*\{)', line)
        if m:
            name = m.group(1)
            if re.search(r'return\s*\(?\s*<|=>.*<\w', content[max(0, line.find(name)):min(len(content), line.find(name)+500)]):
                issues.append(_issue(
                    'component-naming', 'warning', f'Nama Komponen React Bukan PascalCase: {name}', i, s,
                    f'Komponen React "{name}" tidak menggunakan PascalCase. React memperlakukannya sebagai HTML element, bukan komponen.',
                    f'Rename menjadi "{name[0].upper() + name[1:]}". Semua komponen React HARUS dimulai dengan huruf kapital.'))
    return issues


def _check_key_index(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'key=\{[^}]*index\}|key=\{i\}', line):
            issues.append(_issue(
                'key-index', 'warning', 'key={index} pada .map() — Anti-Pattern', i, s,
                f'key={{index}} di baris {i}. Menggunakan index sebagai key menyebabkan bug rendering saat list berubah.',
                'Gunakan ID unik dari data: key={item.id} atau key={item.slug}. Index hanya aman jika list statis dan tidak pernah berubah.'))
    return issues


def _check_missing_key(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\.map\s*\(\s*(?:\([^)]+\)|[\w]+)\s*=>', line):
            # Look ahead for JSX return without key
            block_end = min(i + 10, len(lines))
            block = '\n'.join(lines[i:block_end])
            if re.search(r'<\w', block) and 'key=' not in block[:200]:
                issues.append(_issue(
                    'missing-key', 'error', 'Kemungkinan Missing key Prop di .map()', i, s,
                    f'.map() di baris {i} mungkin tidak memiliki key prop pada elemen yang di-return. Menyebabkan warning dan bug performa.',
                    'Tambahkan key prop pada elemen root di dalam .map(): items.map((item) => <div key={item.id}>...</div>)'))
    return issues


def _check_hooks_in_condition(content: str) -> List[Dict]:
    issues = []
    hook_pattern = re.compile(r'\b(useState|useEffect|useRef|useMemo|useCallback|useContext|useReducer|useLayoutEffect)\s*\(')
    lines = content.split('\n')
    in_condition = 0
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if re.search(r'\b(if|for|while|switch)\s*\(', s):
            in_condition = 5  # Check next 5 lines
        if in_condition > 0:
            if hook_pattern.search(line):
                issues.append(_issue(
                    'hook-in-condition', 'error', 'Hook Dipanggil di Dalam Kondisi/Loop', i, s,
                    f'React Hook dipanggil di dalam kondisi/loop di baris {i}. Melanggar Rules of Hooks.',
                    'Hooks harus selalu dipanggil di top level komponen, TIDAK di dalam if, for, while, atau nested functions. Ini adalah Rules of Hooks yang wajib.'))
            in_condition -= 1
    return issues


def _check_dom_manipulation(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'document\.getElementById|document\.querySelector|document\.getElementsBy', line):
            issues.append(_issue(
                'direct-dom', 'warning', 'Direct DOM Manipulation di React Component', i, s,
                f'Direct DOM manipulation di baris {i}. Bertentangan dengan React\'s virtual DOM paradigm.',
                'Gunakan useRef() hook: const myRef = useRef(); lalu myRef.current untuk akses DOM element dengan aman.'))
    return issues


def _check_class_vs_classname(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*') or s.startswith('<'):
            continue
        if re.search(r'<\w[^>]*\sclass=["\'`]', line) and 'className' not in line:
            issues.append(_issue(
                'class-classname', 'error', 'Menggunakan class= alih-alih className=', i, s,
                f'Atribut class= di JSX baris {i}. Di React/JSX harus menggunakan className=.',
                'Ganti semua class= dengan className= di JSX. class adalah reserved word JavaScript.'))
    return issues


def _check_for_vs_htmlfor(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'<label\b[^>]*\sfor=["\'`]', line) and 'htmlFor' not in line:
            issues.append(_issue(
                'for-htmlfor', 'error', 'Menggunakan for= alih-alih htmlFor= di Label', i, s,
                f'Atribut for= di <label> JSX baris {i}. Di JSX harus menggunakan htmlFor=.',
                'Ganti for= dengan htmlFor= di elemen <label>. for adalah reserved word JavaScript.'))
    return issues


def _check_useeffect_no_deps(content: str) -> List[Dict]:
    issues = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if re.search(r'\buseEffect\s*\(', line):
            block = '\n'.join(lines[i:min(i + 15, len(lines))])
            # Check if the useEffect call spans multiple lines without a dep array
            if '],)' not in block and re.search(r'\)\s*;', block[:100]) and '[' not in '\n'.join(lines[i:min(i+10, len(lines))]):
                if not re.search(r'\[\s*\]', '\n'.join(lines[i-1:min(i+8, len(lines))])):
                    issues.append(_issue(
                        'useeffect-deps', 'warning', 'useEffect Mungkin Tanpa Dependency Array', i, line.strip(),
                        f'useEffect di baris {i} mungkin tidak memiliki dependency array []. Akan dijalankan setiap render (infinite loop risk).',
                        'Selalu sertakan dependency array: useEffect(() => { ... }, []); Kosong [] = sekali saat mount. Isi dengan deps yang relevan.'))
    return issues


def _check_missing_prop_types(content: str) -> List[Dict]:
    """Check if a component file has PropTypes defined (for plain JS, not TS)."""
    if 'TypeScript' in content or ': FC' in content or ': React.FC' in content:
        return []
    if re.search(r'function\s+[A-Z]\w*\s*\(|const\s+[A-Z]\w*\s*=', content):
        if 'PropTypes' not in content and 'propTypes' not in content:
            return [_issue(
                'missing-proptypes', 'info', 'PropTypes Tidak Didefinisikan', 1, '',
                'Komponen React tanpa PropTypes validation. Tidak ada type checking saat development.',
                'Tambahkan PropTypes: import PropTypes from "prop-types"; ComponentName.propTypes = { name: PropTypes.string.isRequired }; Atau migrasikan ke TypeScript untuk type safety yang lebih baik.')]
    return []


# ── Next.js Checks ──────────────────────────────────────────────────────

def _check_nextjs_img(content: str) -> List[Dict]:
    issues = []
    if 'next/image' in content:
        return []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'<img\b', line) and 'next/image' not in content:
            issues.append(_issue(
                'nextjs-img', 'warning', 'Gunakan next/image alih-alih <img>', i, s,
                f'Tag <img> biasa di Next.js baris {i}. Tidak mendapat otomatis optimasi gambar.',
                'Import dan gunakan Image dari Next.js: import Image from "next/image"; <Image src="..." width={} height={} alt="" />',
                'Next.js'))
    return issues


def _check_nextjs_link(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        m = re.search(r'<a\b[^>]*href=["\'](?!//)(?!http)(\/[^"\']*)["\']', line)
        if m and 'next/link' not in content:
            issues.append(_issue(
                'nextjs-link', 'warning', 'Gunakan next/link untuk Internal Navigation', i, s,
                f'<a href="{m.group(1)}"> untuk internal link di baris {i}. Tidak mendapat client-side navigation & prefetching.',
                'Gunakan: import Link from "next/link"; <Link href="' + m.group(1) + '">teks link</Link>',
                'Next.js'))
    return issues


def _check_nextjs_secrets(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'NEXT_PUBLIC_', line) and re.search(r'(?:secret|key|password|token)', line, re.IGNORECASE):
            issues.append(_issue(
                'nextjs-public-secret', 'error', 'Secret Key Exposed via NEXT_PUBLIC_', i, s,
                f'NEXT_PUBLIC_ prefix di baris {i} mengekspos variable ke client-side. Secret tidak boleh NEXT_PUBLIC_!',
                'Variabel secret TIDAK boleh menggunakan prefix NEXT_PUBLIC_. Akses hanya di server-side (getServerSideProps, API routes, Server Components).',
                'Next.js'))
    return issues


def _check_use_client_overuse(content: str) -> List[Dict]:
    if re.search(r'["\']use client["\']', content):
        if not re.search(r'useState|useEffect|useRef|onClick|onChange|onSubmit|addEventListener', content):
            return [_issue(
                'use-client-overuse', 'info', '"use client" Mungkin Tidak Diperlukan', 1, '"use client"',
                '"use client" directive ada tapi tidak ada interactivity (hooks/events). Ini membatasi server-side optimization.',
                'Hapus "use client" jika komponen tidak butuh browser APIs atau React state. Biarkan sebagai Server Component untuk performa lebih baik.',
                'Next.js')]
    return []
