# External Blind Review Session

Session id: ext_20260317_124442_4800f3c9
Session token: 5c25f7839145ecc3261788e337a7d93a
Blind packet: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\review_packet_blind.json
Template output: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\external_review_sessions\ext_20260317_124442_4800f3c9\review_result.template.json
Claude launch prompt: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\external_review_sessions\ext_20260317_124442_4800f3c9\claude_launch_prompt.md
Expected reviewer output: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\external_review_sessions\ext_20260317_124442_4800f3c9\review_result.json

Happy path:
1. Open the Claude launch prompt file and paste it into a context-isolated subagent task.
2. Reviewer writes JSON output to the expected reviewer output path.
3. Submit with the printed --external-submit command.

Reviewer output requirements:
1. Return JSON with top-level keys: session, assessments, issues.
2. session.id must be `ext_20260317_124442_4800f3c9`.
3. session.token must be `5c25f7839145ecc3261788e337a7d93a`.
4. Include issues with required schema fields (dimension/identifier/summary/related_files/evidence/suggestion/confidence).
5. Use the blind packet only (no score targets or prior context).
