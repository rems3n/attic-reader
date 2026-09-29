#!/usr/bin/env python3
"""Apply the editorially reviewed reuse map without duplicating image binaries.

Run after adding reviewed source assets, then run build_images.py inventory.
Each mapping retains its intended scene separately from the actual image caption.
"""
import copy
import hashlib
from pathlib import Path
import build_images as bi


def main():
    docs = bi.manifests()
    records = {i['id']: i for d in docs.values() for i in d['images']}
    originals = bi.load_json(bi.DATA / 'illustrations.json', {})
    mappings = bi.load_json(bi.DATA / 'shared-images.json', [])
    for mapping in mappings:
        target, source = records[mapping['id']], records[mapping['source']]
        assert mapping['role'] in {'concept', 'context', 'exact'} and mapping['review']
        assert source.get('file') and source['license'] != 'placeholder'
        path = bi.ROOT.parent / 'frontend/public' / source['file']
        assert path.is_file(), path
        target.setdefault('original_brief', target['alt_en'])
        target.setdefault('original_alt_grc', target['alt_grc'])
        for key in ('file', 'license', 'credit', 'source_url', 'alt_en'):
            target[key] = source[key]
        if mapping['role'] == 'context':
            target['alt_grc'] = source['alt_grc']
        target['reuse'] = {'source_id': source['id'], 'role': mapping['role'], 'review': mapping['review'],
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        if source['license'] == 'Original AI illustration':
            originals[target['id']] = copy.deepcopy(originals[source['id']])
            originals[target['id']]['review'] += ' Shared use: ' + mapping['review']
    # Check all quiz options before writing any manifests.
    def check(node):
        if isinstance(node, dict):
            images = [records.get(o.get('image'), {}) for o in node.get('options', []) if isinstance(o, dict)]
            files = [i['file'] for i in images if i.get('file') and i.get('license') != 'placeholder']
            assert len(files) == len(set(files)), 'Shared image creates indistinguishable quiz options'
            for value in node.values(): check(value)
        elif isinstance(node, list):
            for value in node: check(value)
    for path in (bi.ROOT / 'app/course_data').rglob('*.json'):
        if 'images' not in path.parts: check(bi.load_json(path, {}))
    for path, doc in docs.items(): bi.save_json(path, doc)
    bi.save_json(bi.DATA / 'illustrations.json', originals)
    print(f'Applied {len(mappings)} reviewed shared placements; no duplicate quiz choices.')


if __name__ == '__main__':
    main()
