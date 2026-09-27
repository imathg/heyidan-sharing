# 在线蒸馏 OPD：抗遗忘、能力合并与训练失效

理解 OPD 的学生采样、OPSD 的特权信息和师生匹配，可以先读 [《OPD 与 OPSD：学生采样、特权信息与抗遗忘边界》](../../briefs/on-policy-distillation/)。它从 OPSD 原论文的双条件策略出发，再比较抗遗忘观察、高概率 token 匹配和 loss 下降却没有效果的情形，说明现有证据能支持哪些机制解释。

## 为领域模型继续叠加能力

[《用 OPD 给领域后训练模型继续叠加能力：组件已有先例，组合仍待验证》](../../briefs/capability-merge-distillation/) 面向已有业务模型的增量训练：从当前领域模型继续，还是回到通用后训练模型重新合入能力？文章按学生起点和旧能力保留方式比较先例；完整组合与两条路径的直接对比仍待验证。

## 区分学生离域、教师偏差与训练控制问题

[《OPD 失效诊断：学生离域、教师偏差与旧轨迹》](../../briefs/opd-training-pathologies/) 适合训练已经运行、但曲线与任务效果脱节时阅读。它先用 OPSD 原论文中的 style-token divergence、teacher 固定方式和 clipping 建立基线，再区分 student state 离域和 teacher 差分偏移，并给出 rollout freshness、selector × learning rate 等实验控制边界。

三篇分别用于理解机制、选择能力合并方案和排查训练故障；第一篇回答 OPSD 到底是什么，第三篇则继续追问 privileged teacher 的差分何时会偏，可按当前问题直接进入。
