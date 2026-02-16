---
description: Fetch website traffic data from SimilarWeb via API with proxy IP rotation
---

Use the fetch_website_flow_analysis_v2 skill to extract SimilarWeb data for the specified domain.

The domain should be passed as the argument (e.g., `/fetch_website_flow_analysis_v2 github.com`).

This is the **recommended** method. It uses SimilarWeb internal APIs with proxy IP rotation,
returning structured JSON data. Faster and more stable than the browser-based v1 approach.

Prerequisites:
- Valid cookie file (run `/sw_login` if expired)
- Python 3.10+ with `requests` package
