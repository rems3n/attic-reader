from app.course import data
from app.course.image_catalog import image_catalog


def test_catalog_covers_every_image_without_counting_candidates_as_complete():
    catalog = image_catalog()
    rows = {i['id']: i for i in catalog['images']}
    assert set(rows) == set(data.load_images())
    assert catalog['summary']['completed'] + catalog['summary']['remaining'] == len(rows)
    candidates = [i for i in rows.values() if i['candidate']]
    assert candidates
    assert all(i['status'] == 'remaining' and i['medium'] == 'pending' for i in candidates)
    assert rows['alphabet-chart']['medium'] == 'diagram'
    assert rows['kyon']['medium'] == 'illustration'
    assert rows['dipylon-oinochoe']['medium'] == 'photo'


def test_catalog_connects_vocabulary_and_story_context_to_real_lessons():
    rows = {i['id']: i for i in image_catalog()['images']}
    assert {'id': 'κυων', 'lemma': 'κύων', 'definition': 'dog'} in rows['kyon']['vocabulary']
    assert any(u['id'] == '1.1' and u['location'].startswith('vocab') for u in rows['kyon']['usages'])
    assert any(u['id'] == '2.1' and 'Ἐλπίδα' in u['context'] for u in rows['panel-2-1-a']['usages'])
    assert rows['hemera']['provenance']['prompt']
    assert any(u['location'].startswith('quiz') for u in rows['hemera']['usages'])
    for row in rows.values():
        for usage in row['usages']:
            if usage['href']:
                assert data.lesson_path(usage['id']).exists()
