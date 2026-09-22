# AtlasRE documentation index

This directory contains current operating guidance, review materials, illustrative examples, and clearly identified historical records. The repository [README](../README.md) is the entry point for installation and a fast local run. Root-level [architecture](../ATLASRE_ARCHITECTURE.md) and [investment committee brief](../INVESTMENT_COMMITTEE_MEMO.md) remain at the repository root because they are GitHub-facing orientation documents rather than task-specific operating guides.

| File | Purpose | Primary audience | Current status |
| --- | --- | --- | --- |
| [OVERVIEW.md](OVERVIEW.md) | Defines the prototype's purpose, boundaries, and a short evaluation path. | External reviewer | Current |
| [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) | Explains formula locations, reconciliation, and reproduction of the illustrative case. | External reviewer | Current |
| [REVIEW_REQUEST.md](REVIEW_REQUEST.md) | Defines the requested scope and boundaries for an independent finance review. | External reviewer | Current |
| [review/REVIEW_CHECKLIST.md](review/REVIEW_CHECKLIST.md) | Provides a structured worksheet for recording review findings. | External reviewer | Current |
| [USING_A_REAL_DEAL.md](USING_A_REAL_DEAL.md) | Describes the local workflow and safeguards for owner-supplied data. | Owner | Current |
| [SECURITY_AND_DATA.md](SECURITY_AND_DATA.md) | States the handling boundaries for confidential or source-backed data. | Owner | Current |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Supplies the short walkthrough for the bundled illustrative demo. | Contributor | Current |
| [case_study.md](case_study.md) | Documents one reproducible illustrative acquisition case and its independent numerical checks. | External reviewer | Current |
| [sample_output/README_ILLUSTRATIVE.md](sample_output/README_ILLUSTRATIVE.md) | Describes the committed illustrative package artifact set. | External reviewer | Current committed artifact |
| [sample_output/investment_committee_memo.md](sample_output/investment_committee_memo.md) | Preserves an illustrative generated screening memorandum. | External reviewer | Current committed artifact |
| [sample_output/investment_committee_report.md](sample_output/investment_committee_report.md) | Preserves an illustrative generated screening report. | External reviewer | Current committed artifact |
| [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) | Retains evidence from an earlier implementation and review-fixes branch. | Owner | Historical record |
| [baseline_audit.md](baseline_audit.md) | Retains the earlier baseline comparison and remediation trail. | Owner | Historical record |

The `sample_output/` directory is a committed illustrative artifact. Its files are not live model output and should be regenerated only through the documented package workflow. The `templates/` directory contains the owner-supplied deal JSON template; it is an input template rather than prose documentation.
