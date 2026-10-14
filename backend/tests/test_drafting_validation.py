from app.agents.drafting import find_problems
from app.schemas import DraftResult

GOOD_BODY = " ".join(["word"] * 80)


def make(subject="Quick idea for your onboarding", body=GOOD_BODY):
    return DraftResult(subject=subject, body=body, gap_referenced="onboarding is manual")


def test_good_draft_has_no_problems():
    assert find_problems(make()) == []


def test_too_short_body_is_rejected():
    assert find_problems(make(body="Too short to be useful."))


def test_too_long_body_is_rejected():
    assert find_problems(make(body=" ".join(["word"] * 200)))


def test_banned_phrase_is_rejected():
    body = "I hope this email finds you well. " + " ".join(["word"] * 70)
    problems = find_problems(make(body=body))
    assert any("i hope this email finds you well" in p.lower() for p in problems)


def test_placeholder_brackets_are_rejected():
    body = GOOD_BODY + " [Your Name]"
    problems = find_problems(make(body=body))
    assert any("bracket" in p.lower() for p in problems)


def test_long_subject_is_rejected():
    subject = " ".join(["many"] * 12)
    assert find_problems(make(subject=subject))


def test_empty_subject_is_rejected():
    assert find_problems(make(subject="   "))