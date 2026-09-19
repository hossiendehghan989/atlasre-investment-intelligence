# Security and data handling

AtlasRE is a local, single-user analytical prototype. It handles user-entered deal assumptions, illustrative market inputs, rent-roll fields, generated screening reports, and model-run metadata. The repository does not provide a secure data room, encryption policy, identity management, access control, retention service, or immutable audit store.

Do **not** use this prototype with sensitive real deal data, personally identifiable information, confidential tenant information, credentials, or regulated records. Use synthetic or appropriately redacted inputs for development and demonstrations. Generated artifacts may contain financial assumptions and should be treated as local working papers.

A production deployment would require authenticated users, role-based permissions, tenant and deal segregation, encryption in transit and at rest, secrets management, immutable audit storage, documented retention and deletion policies, source-document access controls, independent model validation, monitoring, vulnerability management, and legal/compliance review.
