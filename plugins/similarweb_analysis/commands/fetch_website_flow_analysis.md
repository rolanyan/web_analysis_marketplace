---
description: Fetch website traffic overview and referral data from SimilarWeb
---

Use the fetch_website_flow_analysis skill to extract SimilarWeb data for the specified domain.

The domain should be passed as the argument (e.g., `/fetch_website_flow_analysis github.com`).

Follow the skill's workflow to:
1. Ensure dev-browser server is running
2. Navigate to SimilarWeb and extract website performance overview
3. Navigate to referrals page and extract incoming referral table
4. Save results to web_data/{domain}/
