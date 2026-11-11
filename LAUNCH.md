# Launch drafts

Review each community's current rules and obtain any required permission before posting. Do not post automatically.

**Show HN title:** Show HN: Agent Replay – offline regression checks for tool calls

**Show HN draft:** I built a small Python tool for comparing agent tool-call traces and running an agent against recorded mock outcomes. It checks names, arguments, order, and error outcomes. You must supply a new run to detect behavior changes; it doesn't magically rerun stored traces. I'd welcome feedback on matching rules and the mock API.

**r/MachineLearning draft:** I have an early tool-call regression testing prototype. It compares independently observed trajectories and provides deterministic mock results. What evaluation pitfalls would you prioritize? I'll check the current research/project posting rules first.

**r/LocalLLaMA draft:** For local agent experiments, I made an offline tool-call comparison prototype. It doesn't call a model and supports synthetic fixtures and mocked failures. How do you handle nondeterministic arguments in regression tests?

**r/Python draft:** I built a typed Python CLI and pytest decorator for testing agent tool-call sequences. The test must produce actual calls; mock tools can also inject recorded failures. Feedback on API ergonomics is welcome.

**X thread:** 1/ Agent tool calls can regress even when the final answer looks plausible. 2/ Agent Replay compares a new trace with a baseline and can return recorded mock outcomes. 3/ It is offline, supports a narrow provider import subset, and requires you to connect your own agent. Feedback welcome.

**LinkedIn draft:** Testing an agent means checking the interactions that led to its answer. This prototype compares observed tool calls and exercises agent code against mock results, including errors. It doesn't claim to capture or rerun agents automatically. I'm interested in feedback from teams testing agent workflows.

**dev.to outline:** Problem and example regression; trace format; collect actual calls; compare in CI; mock a tool failure; matching tradeoffs; limitations and future work.

**Awesome lists to investigate** (check scope and contribution rules before submission): [awesome-python](https://github.com/vinta/awesome-python), [awesome-testing](https://github.com/TheJambo/awesome-testing), [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps), [awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents), [awesome-llm](https://github.com/Hannibal046/Awesome-LLM).
