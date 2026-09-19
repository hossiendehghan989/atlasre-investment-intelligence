# Deploying AtlasRE to Streamlit Community Cloud

AtlasRE is configured for Streamlit Community Cloud with `dashboard.py` as the entrypoint and `requirements.txt` in the repository root. Community Cloud runs an app from the repository root, expects configuration at `.streamlit/config.toml`, and permits the app file to remain at the root. [1] The checked-in configuration uses a light neutral palette and disables usage-stat collection.

## Pre-deployment check

Run the following commands from the repository root on Python 3.11, which is the version used by the hosted app and local release checks:

```bash
python -m pip install -r requirements.lock
ruff check .
python -m pytest -q
streamlit run dashboard.py
```

The dashboard reads its bundled market-input CSV using a path resolved from `dashboard.py`. It builds review ZIP files and Excel workbooks in memory and does not write files during normal dashboard use. The separate CLI command `python generate_committee_report.py` writes to `artifacts/`; do not use that command as the Community Cloud entrypoint.

## Community Cloud settings

1. Push the desired commit to GitHub. The review branch is `review-fixes`; select that branch for review deployment, or select the later branch that contains the commit you intend to publish.
2. At [share.streamlit.io](https://share.streamlit.io/), choose **Create app**, then select the repository and branch. Community Cloud accepts a repository, branch, and entrypoint path in the creation form. [2]
3. Set the main file path to `dashboard.py`.
4. Open **Advanced settings** and select **Python 3.11**. Community Cloud supports selecting the Python version there; selecting it explicitly matches the hosted app and CI validation environment. [2]
5. Leave the secrets field empty. This prototype has no secret, credential, or external-service requirement.
6. Deploy and inspect the build log. The first page should display the default **ILLUSTRATIVE** review case, including source status `REVIEW REQUIRED`.

## Dependency and resource notes

`requirements.txt` contains the runtime dependencies, including `openpyxl` for the reconciliation workbook. Community Cloud recognizes a root-level `requirements.txt` for pip installation. [3] `requirements.lock` remains the exact local and CI installation record; it is not the Community Cloud dependency declaration.

The dashboard and CLI both use 5,000 seeded simulations with seed 42. The dashboard computes its risk summary on first load and creates the same 5,000-simulation review ZIP when a user selects **Prepare review files**. No system package is required, so `packages.txt` is intentionally absent.

## Smoke test after deployment

Confirm the following before sharing the app URL:

- The default dashboard loads without an exception and shows `REJECT / REWORK` for the illustrative case.
- **Risk tail detail** opens and shows seeded downside values.
- **Prepare review files** shows the progress status and enables the ZIP download.
- **Download Excel reconciliation** returns an `.xlsx` file with the Control, Inputs, Annual NOI, Debt Schedule, Cash Flows, Reconciliation, and Lineage sheets.
- Changing an assumption invalidates the prior review-package download until new files are prepared.

If deployment fails, first verify that the selected branch contains `dashboard.py`, `requirements.txt`, and `.streamlit/config.toml`; then read the Community Cloud build log. Logs are visible to repository writers. [2]

## References

[1]: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization "File organization for your Community Cloud app"
[2]: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy "Deploy your app on Community Cloud"
[3]: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies "App dependencies for your Community Cloud app"
