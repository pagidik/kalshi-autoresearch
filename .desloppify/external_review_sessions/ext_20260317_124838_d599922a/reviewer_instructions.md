# External Blind Review Session

Session id: ext_20260317_124838_d599922a
Session token: 7e50bac9f85ad4549a78759ed7ac58e6
Blind packet: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\review_packet_blind.json
Template output: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\external_review_sessions\ext_20260317_124838_d599922a\review_result.template.json
Claude launch prompt: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\external_review_sessions\ext_20260317_124838_d599922a\claude_launch_prompt.md
Expected reviewer output: C:\Users\kisho\clawd\projects\kalshi-autoresearch-oss\.desloppify\external_review_sessions\ext_20260317_124838_d599922a\review_result.json

Happy path:
1. Open the Claude launch prompt file and paste it into a context-isolated subagent task.
2. Reviewer writes JSON output to the expected reviewer output path.
3. Submit with the printed --external-submit command.

Reviewer output requirements:
1. Return JSON with top-level keys: session, assessments, issues.
2. session.id must be `ext_20260317_124838_d599922a`.
3. session.token must be `7e50bac9f85ad4549a78759ed7ac58e6`.
4. Include issues with required schema fields (dimension/identifier/summary/related_files/evidence/suggestion/confidence).
5. Use the blind packet only (no score targets or prior context).
