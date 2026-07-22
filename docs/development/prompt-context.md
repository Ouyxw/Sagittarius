# Prompt Context Standards

Status: `Template`
Roadmap: Cross-phase AI-assisted development workflow
Version: `prompt-context/v1`
Last reviewed: 2026-07-03


This document standardizes prompts for AI-assisted Sagittarius development. It complements [`AGENTS.md`](../../AGENTS.md) and [`agent-workflow-template.md`](agent-workflow-template.md). Use these prompts as templates; branch owners may customize wording, but should preserve the context-recovery, no-unapproved-editing, test, documentation, and evidence gates.

本文件用于标准化 Sagittarius 项目中的 AI 协同开发 prompt。它不是固定万能 prompt，而是一组可裁剪模板。开发者可以根据 feature/develop/release/test 分支调整措辞，但应保留上下文恢复、未经确认不改代码、测试、文档和证据门槛。

## Prompt Principles / Prompt 原则

- The first prompt in a new session should recover context and classify the task before implementation.
- The agent should not edit code during planning/status prompts unless explicitly authorized.
- Long-running branches should maintain a branch-local workflow document, for example `docs/development/branches/phase14-noise-models.md`.
- Branch-local workflow documents track progress; formal docs record durable project behavior.
- Prompts should name the target roadmap phase, requirement item, source specs, and expected validation.
- Public claims, release readiness, PyPI support, CUDA validation, or performance improvements require retained evidence.

中文要点：

- 新会话的第一条 prompt 应先恢复上下文并判断任务影响面，而不是直接实现。
- 计划和状态类 prompt 中，除非开发者明确授权，否则 AI 不应修改代码。
- 长周期分支建议维护分支工作文档，例如 `docs/development/branches/phase14-noise-models.md`。
- 分支工作文档记录过程，正式 docs 描述项目最终状态。
- prompt 应明确目标 phase、需求项、关联 specs 和验证方式。
- 发布、性能、CUDA、PyPI 等声明必须有保留证据支撑。

## Prompt 1: Start A New Feature Branch / 启动新功能分支

Use this after creating a feature or test branch. This prompt should not allow code edits.

```text
I am starting a new branch for <roadmap phase / feature / test scope>.

Please start the AI collaboration workflow:
1. Read and follow AGENTS.md.
2. Read docs/development/agent-workflow-template.md.
3. Recover context using the template's Context Recovery section.
4. Read docs/development/requirements.md for <target phase or requirement item>.
5. List the relevant SPEC/docs files for this task.
6. Create or update a Branch Customization Block at <branch workflow doc path>, for example docs/development/branches/<branch-name>.md.
7. Include Branch Baseline, Scope, Requirement Items, Cross-Phase Dependencies, Required Context, Change Surface, Required Validation, and Handoff Requirements.
8. Do not edit implementation code yet.
```

中文版本：

```text
我现在新开了 <roadmap phase / feature / test scope> 分支。

请开启 AI 协同开发流程：
1. 读取并遵守 AGENTS.md。
2. 读取 docs/development/agent-workflow-template.md。
3. 按模板中的 Context Recovery 恢复上下文。
4. 读取 docs/development/requirements.md 中 <目标 Phase 或需求项>。
5. 列出本任务涉及的 SPEC/docs 文件。
6. 创建或更新分支工作文档 <branch workflow doc path>，例如 docs/development/branches/<branch-name>.md。
7. 写入 Branch Baseline、Scope、Requirement Items、Cross-Phase Dependencies、Required Context、Change Surface、Required Validation 和 Handoff Requirements。
8. 暂时不要修改实现代码。
```

## Prompt 2: Ask For The Smallest P0 Slice / 请求最小 P0 切片

Use this after the Branch Customization Block exists.

```text
Read the current branch workflow document at <path>.
List the smallest P0 slice for the highest-priority requirement item.
Include:
- requirement items covered;
- in scope and out of scope;
- acceptance checks;
- code surfaces;
- tests to add or update;
- docs to update;
- schema/artifact impact;
- risks and blocked assumptions.
Do not edit code yet.
```

中文版本：

```text
请读取当前分支工作文档 <path>。
针对最高优先级需求项，列出最小 P0 切片。
必须包含：
- 覆盖的 requirement items；
- in scope 和 out of scope；
- acceptance checks；
- 代码影响面；
- 需要新增或更新的测试；
- 需要更新的文档；
- schema/artifact 影响；
- 风险和阻塞假设。
暂时不要修改代码。
```

## Prompt 3: Authorize Implementation / 授权实现

Use this only after reviewing the P0 slice.

```text
I approve the proposed slice <slice id>.
Please implement only this slice.
Before editing, check git status and identify existing uncommitted changes.
After implementation:
- run the targeted tests listed in the branch workflow document;
- update formal docs required by docs/development/status.md;
- update the branch workflow document's Requirement Items, Current Slice, Validation Log, and Progress Log;
- summarize changed surfaces, tests run, docs updated, and residual risks.
```

中文版本：

```text
我确认实现切片 <slice id>。
请只实现这个切片。
修改前先检查 git status，并识别已有未提交改动。
实现后：
- 运行分支工作文档中列出的 targeted tests；
- 按 docs/development/status.md 更新正式文档；
- 更新分支工作文档中的 Requirement Items、Current Slice、Validation Log 和 Progress Log；
- 总结代码影响面、测试结果、文档更新和残余风险。
```

## Prompt 4: Resume An Existing Branch / 恢复已有分支上下文

Use this when opening a new session on an existing feature branch.

```text
Read the current branch workflow document at <path> and resume context.
Report:
1. base commit and current working tree status;
2. Requirement Items grouped by status;
3. completed and verified items;
4. implemented but unverified or undocumented items;
5. blocked or deferred items;
6. recommended next requirement priority;
7. the smallest slice for the highest-priority item, including acceptance checks, tests, docs, and risks.
Do not edit code yet.
```

中文版本：

```text
请读取当前分支工作文档 <path> 并恢复上下文。
请报告：
1. base commit 和当前工作区状态；
2. 按状态分组的 Requirement Items；
3. 已完成且已验证的项；
4. 已实现但未验证或文档未同步的项；
5. blocked 或 deferred 项；
6. 建议的下一步需求优先级；
7. 最高优先级需求项的最小切片，包括 acceptance checks、测试、文档和风险。
暂时不要修改代码。
```

## Prompt 5: Commit-Ready Handoff / 提交前交付检查

Use this after a slice appears complete and before committing.

```text
Prepare a commit-ready handoff for the current slice.
Please inspect git diff and report:
- files changed by category: code, tests, docs, branch workflow docs;
- requirement items updated;
- validation commands and results;
- artifacts or schema changes;
- formal docs updated;
- branch workflow document updates;
- residual risks and follow-up items.
Also draft a concise commit message following AGENTS.md.
Do not create the commit unless explicitly asked.
```

中文版本：

```text
请为当前切片准备提交前交付检查。
请检查 git diff 并报告：
- 按类别列出的变更文件：代码、测试、正式文档、分支工作文档；
- 已更新的 requirement items；
- 验证命令和结果；
- artifact 或 schema 变更；
- 已更新的正式文档；
- 分支工作文档更新；
- 残余风险和 follow-up。
同时按 AGENTS.md 起草一个简洁 commit message。
除非我明确要求，不要创建 commit。
```

## Prompt 6: Complete A Phase Or Feature / 完成 Phase 或 Feature

Use this when all planned requirement items for a branch are complete or intentionally deferred.

```text
Read the branch workflow document at <path> and prepare a phase/feature conclusion.
Include:
- completed requirement items;
- verified tests and artifacts;
- deferred or blocked items with reasons;
- formal docs that were updated;
- docs that still need updates;
- known limitations changed or remaining;
- suggested branch-local document disposition: remove, retain, or extract into formal docs/PR description.
Do not edit code unless explicitly asked.
```

中文版本：

```text
请读取分支工作文档 <path>，并准备 Phase/Feature 结论。
包括：
- 已完成的 requirement items；
- 已验证的测试和 artifacts；
- deferred 或 blocked 项及原因；
- 已更新的正式文档；
- 仍需更新的文档；
- 已改变或仍存在的 known limitations；
- 对分支工作文档的处理建议：删除、保留，或提炼到正式文档/PR 描述。
除非我明确要求，不要修改代码。
```

## Prompt 7: Review Mode / 审查模式

Use this when asking the agent to review existing work rather than implement.

```text
Review the current branch against AGENTS.md, docs/development/agent-workflow-template.md, and the branch workflow document at <path>.
Focus on bugs, missing tests, schema/artifact incompatibility, docs drift, parity risks, and unsupported claims.
List findings by severity with file references.
Do not modify files.
```

中文版本：

```text
请根据 AGENTS.md、docs/development/agent-workflow-template.md 和分支工作文档 <path> 审查当前分支。
重点关注 bug、缺失测试、schema/artifact 不兼容、文档漂移、parity 风险和不受支持的声明。
按严重程度列出 findings，并给出文件引用。
不要修改文件。
```

## Required Branch Workflow Sections / 分支工作文档必备章节

A long-running feature branch should maintain these sections:

- Branch Baseline
- Scope
- Requirement Items
- Cross-Phase Dependencies
- Required Context
- Change Surface
- Current Slice
- Required Validation
- Validation Log
- Progress Log
- Handoff Requirements
- Conclusion

Long branches may add more sections, but should not remove these without recording a reason.

## Anti-Patterns / 避免的 Prompt 模式

Avoid prompts such as:

```text
Just implement Phase 14.
Fix everything.
Make it production ready.
Run whatever tests are needed.
Update docs if needed.
```

These prompts are too broad and hide acceptance criteria. Prefer prompts that name the requirement item, slice, specs, tests, docs, and handoff requirements.

避免使用过宽泛的 prompt，例如：

```text
直接实现 Phase 14。
把所有问题都修好。
让它 production ready。
需要什么测试就跑什么。
如果需要就更新文档。
```

这类 prompt 没有清晰验收标准。应明确需求项、切片、规格文档、测试、文档和交付要求。
