"""The beginner course: lessons, tests, skills, drills.

Content lives in ``app/course_data`` as JSON (see docs/COURSE_PLAN.md §5).
``data`` loads and resolves it, ``validate`` enforces the authoring rules
(controlled vocabulary, engine-checked forms, image licences), ``drill``
generates morphology items from the lexicon, and ``grade`` scores a
learner's response the same way the frontend does.
"""

from .data import (  # noqa: F401
    DATA_DIR,
    CourseError,
    all_entries,
    course_index,
    entry_by_id,
    entry_lessons,
    extra_entries,
    lesson_ids,
    load_course,
    load_images,
    load_lesson,
    load_skills,
    load_test,
    resolve_lesson,
    resolve_test,
    vocab_scope,
)
