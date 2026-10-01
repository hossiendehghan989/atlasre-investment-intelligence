# Contributing to AtlasRE

Thank you for helping improve a transparent, illustrative underwriting prototype.

## Before opening an issue or pull request

```bash
python -m pip install -r requirements.lock
ruff check .
python -m pytest -q
```

Please keep all examples synthetic or illustrative. Never upload owner-supplied deal data, credentials, personal data, or confidential documents.

## Good contributions

- Add or improve a focused regression test.
- Improve model validation, reconciliation, or reviewer documentation.
- Make assumptions and limitations more explicit.
- Improve reproducibility, accessibility, or deployment safety.

## Pull request checklist

- [ ] The change has a focused purpose.
- [ ] Tests and lint pass locally.
- [ ] New behavior has regression coverage.
- [ ] Assumptions, limitations, and data boundaries are documented.
- [ ] No sensitive or proprietary data is included.
