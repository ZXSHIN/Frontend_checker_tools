"""Vue.js quality rules (Vue 2 & Vue 3)."""
import re
from typing import List, Dict


def _issue(rule, severity, name, line, snippet, message, fix, framework='Vue.js'):
    return {'rule': rule, 'severity': severity, 'name': name, 'line': line,
            'snippet': (snippet or '').strip()[:120], 'message': message, 'fix': fix, 'framework': framework}


def check_all(content: str, filename: str) -> List[Dict]:
    issues = []
    issues.extend(_check_vfor_key(content))
    issues.extend(_check_vfor_vif_same(content))
    issues.extend(_check_component_name(filename))
    issues.extend(_check_prop_mutation(content))
    issues.extend(_check_vhtml_security(content))
    issues.extend(_check_parent_access(content))
    issues.extend(_check_missing_define_emits(content))
    issues.extend(_check_vfor_index_key(content))
    return issues


def _check_vfor_key(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if re.search(r'v-for=', line, re.IGNORECASE):
            if ':key=' not in line and 'v-bind:key=' not in line:
                issues.append(_issue(
                    'vue-vfor-key', 'error', 'v-for Tanpa :key Binding', i, s,
                    f'v-for di baris {i} tidak memiliki :key. Wajib untuk performa rendering yang benar.',
                    'Selalu tambahkan :key yang unik: <div v-for="item in items" :key="item.id">. Gunakan ID unik dari data, bukan index.'))
    return issues


def _check_vfor_vif_same(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if re.search(r'v-for=', line) and re.search(r'v-if=', line):
            issues.append(_issue(
                'vue-vfor-vif', 'error', 'v-for dan v-if pada Elemen yang Sama', i, line.strip(),
                f'v-for + v-if di elemen yang sama (baris {i}). v-if akan berjalan setiap iterasi — sangat tidak efisien.',
                'Pindahkan v-if ke elemen parent (gunakan <template v-if>), atau filter data dengan computed property sebelum v-for.'))
    return issues


def _check_component_name(filename: str) -> List[Dict]:
    import os
    base = os.path.splitext(os.path.basename(filename))[0]
    if re.match(r'^[a-z][a-z\-]*$', base) and '-' not in base:
        return [_issue(
            'vue-component-name', 'warning', f'Nama File Komponen Bukan Multi-Word: {base}', 1, filename,
            f'Komponen Vue "{base}" hanya satu kata. Vue Style Guide merekomendasikan nama multi-kata.',
            'Rename menjadi nama yang lebih deskriptif dan multi-kata, contoh: UserCard.vue, AppHeader.vue, BaseButton.vue.')]
    return []


def _check_prop_mutation(content: str) -> List[Dict]:
    issues = []
    # Look for patterns that suggest prop mutation
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\bprops\.\w+\s*=', line) or re.search(r'\bthis\.\$props\.\w+\s*=', line):
            issues.append(_issue(
                'vue-prop-mutation', 'error', 'Mutasi Langsung pada Props', i, s,
                f'Props di-mutate langsung di baris {i}. Melanggar prinsip one-way data flow Vue.',
                'Props bersifat read-only. Emit event ke parent: this.$emit("update:value", newValue) atau gunakan v-model. Jika perlu, copy ke data local terlebih dahulu.'))
    return issues


def _check_vhtml_security(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if re.search(r'v-html=', line, re.IGNORECASE):
            issues.append(_issue(
                'vue-vhtml', 'error', 'v-html dengan Data Dinamis — XSS Risk', i, line.strip(),
                f'v-html di baris {i} dapat menyebabkan XSS jika data berasal dari user input atau API yang tidak terpercaya.',
                'Jangan gunakan v-html dengan data yang tidak di-sanitize. Gunakan DOMPurify.sanitize() sebelum binding ke v-html, atau gunakan teks biasa dengan {{ }} binding.'))
    return issues


def _check_parent_access(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s.startswith('//') or s.startswith('*'):
            continue
        if re.search(r'\bthis\.\$parent\b|\$parent\.', line):
            issues.append(_issue(
                'vue-parent-access', 'warning', 'Akses $parent — Tight Coupling', i, s,
                f'this.$parent di baris {i}. Menciptakan tight coupling antar komponen yang sulit di-maintain.',
                'Gunakan emit events, provide/inject, atau Vuex/Pinia untuk komunikasi antar komponen. Hindari $parent access.'))
    return issues


def _check_missing_define_emits(content: str) -> List[Dict]:
    if '<script setup>' in content or '<script setup lang=' in content:
        if re.search(r'\$emit\s*\(|emit\s*\(', content):
            if 'defineEmits' not in content:
                return [_issue(
                    'vue-define-emits', 'warning', 'defineEmits Tidak Dideklarasikan', 1, '',
                    'Komponen menggunakan emit() tapi tidak mendefinisikan defineEmits(). Events tidak terdokumentasi.',
                    'Tambahkan: const emit = defineEmits(["update:modelValue", "submit"]); di dalam <script setup> untuk mendokumentasikan semua events.')]
    return []


def _check_vfor_index_key(content: str) -> List[Dict]:
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if re.search(r'v-for=["\']\([^,)]+,\s*index\)', line) or re.search(r'v-for=["\'].*in\s', line):
            if re.search(r':key=["\']?\$?index', line):
                issues.append(_issue(
                    'vue-index-key', 'warning', ':key Menggunakan Index — Anti-Pattern', i, line.strip(),
                    f':key="index" di baris {i}. Menggunakan index menyebabkan bug rendering saat item ditambah/hapus/diurutkan.',
                    'Gunakan :key="item.id" atau properti unik lainnya. Index hanya aman untuk list yang benar-benar statis.'))
    return issues
