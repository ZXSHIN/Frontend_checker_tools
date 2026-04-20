"""
Framework & Language Auto-Detector
Detects frameworks/languages from file content and package.json
"""
import re
import json
from typing import List, Optional, Dict


FRAMEWORK_META = {
    # bg = hex approximation of rgba(r,g,b,0.12) blended over #0a0a14 background
    'react':           {'label': 'React',            'color': '#61dafb', 'bg': '#142330', 'icon': '⚛️'},
    'nextjs':          {'label': 'Next.js',          'color': '#e0e0e0', 'bg': '#23232c', 'icon': '▲'},
    'vue':             {'label': 'Vue.js',           'color': '#42b883', 'bg': '#111f21', 'icon': '💚'},
    'nuxt':            {'label': 'Nuxt.js',          'color': '#00dc82', 'bg': '#092321', 'icon': '🟢'},
    'angular':         {'label': 'Angular',          'color': '#dd0031', 'bg': '#230917', 'icon': '🅰️'},
    'svelte':          {'label': 'Svelte',           'color': '#ff3e00', 'bg': '#271012', 'icon': '🔥'},
    'sveltekit':       {'label': 'SvelteKit',        'color': '#ff3e00', 'bg': '#271012', 'icon': '⚙️'},
    'typescript':      {'label': 'TypeScript',       'color': '#3178c6', 'bg': '#0f1729', 'icon': 'TS'},
    'tailwind':        {'label': 'Tailwind CSS',     'color': '#38bdf8', 'bg': '#101f2f', 'icon': '🎨'},
    'scss':            {'label': 'SCSS/SASS',        'color': '#cc6699', 'bg': '#211524', 'icon': '💜'},
    'bootstrap':       {'label': 'Bootstrap',        'color': '#7952b3', 'bg': '#171327', 'icon': 'BS'},
    'styledcomponents':{'label': 'Styled Comp.',     'color': '#db7093', 'bg': '#231623', 'icon': '💅'},
    'html':            {'label': 'HTML5',            'color': '#e44d26', 'bg': '#241216', 'icon': '🌐'},
    'css':             {'label': 'CSS3',             'color': '#1572b6', 'bg': '#0b1627', 'icon': 'CS'},
    'javascript':      {'label': 'JavaScript',       'color': '#f7df1e', 'bg': '#262415', 'icon': 'JS'},
}


def detect_frameworks(content: str, package_json: Optional[Dict] = None) -> List[Dict]:
    """Detect frameworks from combined file content and package.json."""
    detected = set()

    # ── 1. package.json based detection ──────────────────────────────
    if package_json:
        deps = {}
        deps.update(package_json.get('dependencies', {}))
        deps.update(package_json.get('devDependencies', {}))

        pkg_map = {
            'react': 'react',
            'next': 'nextjs',
            'vue': 'vue',
            'nuxt': 'nuxt',
            '@angular/core': 'angular',
            'svelte': 'svelte',
            '@sveltejs/kit': 'sveltekit',
            'typescript': 'typescript',
            'tailwindcss': 'tailwind',
            'bootstrap': 'bootstrap',
            'styled-components': 'styledcomponents',
        }
        for pkg, fw in pkg_map.items():
            if pkg in deps:
                detected.add(fw)

    # ── 2. Code-pattern based detection ─────────────────────────────
    patterns = [
        ('react',           r"from\s+['\"]react['\"]|import\s+React|useState\s*\(|useEffect\s*\(|useRef\s*\(|useMemo\s*\(|useCallback\s*\(|useContext\s*\(|className="),
        ('nextjs',          r"from\s+['\"]next/|getServerSideProps|getStaticProps|getStaticPaths|'use\s+client'|\"use\s+client\"|useRouter.*next|NextPage|GetServerSideProps"),
        ('vue',             r"<template>|from\s+['\"]vue['\"]|defineComponent\s*\(|Vue\.createApp|v-for=|v-if=|v-model=|defineProps\s*\(|defineEmits\s*\(|ref\s*\(<|reactive\s*\("),
        ('nuxt',            r"useNuxtApp\s*\(|definePageMeta\s*\(|useFetch\s*\(|useAsyncData\s*\(|from\s+['\"]#app['\"]"),
        ('angular',         r"@Component\s*\(|@NgModule\s*\(|@Injectable\s*\(|@Input\s*\(\)|@Output\s*\(\)|from\s+['\"]@angular/|ngOnInit|ngOnDestroy|\*ngFor|\*ngIf|\[\(ngModel\)\]"),
        ('svelte',          r"\{#each\s|\{#if\s|on:click|on:submit|export\s+let\s+\w+|from\s+['\"]svelte"),
        ('sveltekit',       r"from\s+['\"]@sveltejs/kit['\"]|\$app/|definePageConfig|load\s*\(\s*\{"),
        ('typescript',      r":\s*(string|number|boolean|void|any|never|unknown|object)\b|interface\s+\w+\s*\{|type\s+\w+\s*=|enum\s+\w+\s*\{|<\w+>\s*\(|as\s+\w+(?!-)"),
        ('tailwind',        r'class(?:Name)?=["\'][^"\']*(?:bg-\w|text-\w+-\d|flex\b|grid\b|p-\d|m-\d|w-\d|h-\d|rounded|shadow|border-)[^"\']*["\']'),
        ('scss',            r'\$[\w-]+\s*:|@mixin\s+\w|@include\s+\w|&\s*[:\[.]'),
        ('bootstrap',       r'class=["\'][^"\']*(?:btn\b|col-\d|container\b|row\b|card\b|navbar\b|modal\b|alert\b|badge\b|form-control)[^"\']*["\']'),
        ('styledcomponents', r'styled\.\w+`|styled\(\w+\)`|css`[^`]|createGlobalStyle`'),
    ]

    for fw, pattern in patterns:
        if re.search(pattern, content, re.MULTILINE):
            detected.add(fw)

    # ── 3. Base language fallbacks ────────────────────────────────────
    if not any(f in detected for f in ('react', 'vue', 'angular', 'svelte')):
        if re.search(r'<!DOCTYPE|<html\b|<head\b|<body\b', content, re.IGNORECASE):
            detected.add('html')
        if re.search(r'function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=|=>\s*[{\(]', content):
            if 'typescript' not in detected:
                detected.add('javascript')

    if re.search(r'\{|@media|:[^:]+\{', content) and not any(
        f in detected for f in ('react', 'vue', 'angular', 'svelte', 'tailwind', 'scss')
    ):
        if not re.search(r'function|const|let|var|import|export', content):
            detected.add('css')

    # ── 4. Return with metadata ───────────────────────────────────────
    result = []
    for fw in detected:
        meta = FRAMEWORK_META.get(fw, {
            'label': fw.capitalize(),
            'color': '#888',
            'bg': 'rgba(136,136,136,0.12)',
            'icon': '📦'
        })
        result.append({'id': fw, **meta})

    return result
