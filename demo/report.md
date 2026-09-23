# A broad abstract meets one narrow experiment

PaperCourt evidence report

Arithmetic and selected metadata are script-checked. Support assessments are model analysis, not academic verdicts. Missing evidence means unknown. Proposed checks have not been run.

Case SHA-256: `43b9117f8110ad27b01ff6c3bc447d03c8ab632176b6907a46399e73c30b1822`

| Claim | Model assessment | Numeric checks | Selected conditions |
| --- | --- | --- | --- |
| [C1](#c1) | limited | not checked | not checked |
| [C2](#c2) | supported_within_scope | consistent | not_applicable |
| [C3](#c3) | conflicting_evidence | inconsistent | aligned |
| [C4](#c4) | limited | consistent | different |
| [C5](#c5) | unknown | not checked | not checked |
| [C6](#c6) | supported_within_scope | consistent | aligned |

## C1

Sprout improves classification accuracy across all image datasets and compute budgets\.

[paper:7](evidence/paper.md#line-7)

**Model analysis: limited**

The supplied evidence covers MiniShapes at 10 epochs\. It cannot establish improvement across all image datasets and compute budgets\.

Evidence:

- [paper:16](evidence/paper.md#line-16)
- [paper:27](evidence/paper.md#line-27)
- [results:2 \{"id": "sprout"\}](evidence/results.md#line-2)
- [results:3 \{"id": "linear"\}](evidence/results.md#line-3)

**Limitations:** No other dataset or training budget is supplied\. This is a scope gap, not a demonstrated counterexample\.

**Minimum next check (proposed):** At a predeclared 1\-epoch budget on MiniShapes, compare Sprout and Linear with the same split, tuning budget, metric, and seeds; report the paired per\-seed differences\.

**Observable falsifier:** A controlled setting where Sprout has no positive mean accuracy difference would contradict the universal improvement claim\.

## C2

On MiniShapes test data under the fixed 10\-epoch protocol, Sprout reaches 82\.0% accuracy\.

[paper:8](evidence/paper.md#line-8)

**Model analysis: supported_within_scope**

The qualified sentence matches the reported aggregate of 82\.0% for the specified setting\.

Evidence:

- [results:2 \{"id": "sprout"\}](evidence/results.md#line-2)
- [paper:17](evidence/paper.md#line-17)
- [paper:18](evidence/paper.md#line-18)

**Script check**

value: consistent — computed 82\.0; claimed 82\.0 ± 0\.05 percent\. Selected conditions: not\_applicable\.

- [results:2 \[value\] \{"id": "sprout"\}](evidence/results.md#line-2)

**Limitations:** Only an aggregate is supplied\. Neither individual seed scores nor statistical significance can be recovered\.

**Minimum next check (proposed):** Recompute the unweighted mean from the three original evaluation logs under fixed\-v1\.

**Observable falsifier:** An independently recomputed mean outside 82\.0 \+/\- 0\.05 percentage points would conflict with the stated rounded value\.

## C3

Under that protocol, Sprout exceeds Linear by 5\.0 percentage points\.

[paper:9](evidence/paper.md#line-9)

**Model analysis: conflicting_evidence**

The supplied aggregates imply a 2\.0 percentage\-point difference, which conflicts with the quoted 5\.0\.

Evidence:

- [results:2 \{"id": "sprout"\}](evidence/results.md#line-2)
- [results:3 \{"id": "linear"\}](evidence/results.md#line-3)

**Script check**

difference: inconsistent — computed 2\.0; claimed 5\.0 ± 0\.05 percentage points\. Selected conditions: aligned\.

- [results:2 \[value\] \{"id": "sprout"\}](evidence/results.md#line-2)
- [results:3 \[value\] \{"id": "linear"\}](evidence/results.md#line-3)
- dataset: aligned — \["MiniShapes", "MiniShapes"\]
- split: aligned — \["test", "test"\]
- metric: aligned — \["accuracy", "accuracy"\]
- unit: aligned — \["percent", "percent"\]
- protocol: aligned — \["fixed\-v1", "fixed\-v1"\]
- budget: aligned — \["10 epochs", "10 epochs"\]
- seeds: aligned — \["11\|22\|33", "11\|22\|33"\]
- aggregation: aligned — \["mean", "mean"\]

**Limitations:** This checks agreement with supplied aggregates; it does not establish which version of the paper or results is authoritative\.

**Minimum next check (proposed):** Reconcile the two aggregate values against the original evaluation logs and the manuscript version\.

**Observable falsifier:** If the authoritative values remain 82\.0 and 80\.0, the 5\.0\-point statement is contradicted\.

## C4

Under identical hardware and batch settings, Sprout is 2\.0 times faster than Linear\.

[paper:10](evidence/paper.md#line-10)

**Model analysis: limited**

The arithmetic ratio is 2\.0, but the timing rows use different hardware\. The identical\-hardware premise conflicts with the recorded settings\.

Evidence:

- [runtime:1 \(JSON /0\) \{"id": "sprout"\}](evidence/runtime.md#line-1)
- [runtime:1 \(JSON /1\) \{"id": "linear"\}](evidence/runtime.md#line-1)
- [paper:23](evidence/paper.md#line-23)

**Script check**

ratio: consistent — computed 2; claimed 2\.0 ± 0\.01 times\. Selected conditions: different\.

- [runtime:1 \(JSON /1\) \[value\] \{"id": "linear"\}](evidence/runtime.md#line-1)
- [runtime:1 \(JSON /0\) \[value\] \{"id": "sprout"\}](evidence/runtime.md#line-1)
- dataset: aligned — \["MiniShapes", "MiniShapes"\]
- split: aligned — \["test", "test"\]
- metric: aligned — \["latency", "latency"\]
- unit: aligned — \["milliseconds", "milliseconds"\]
- protocol: aligned — \["timing\-v1", "timing\-v1"\]
- hardware: different — \["CPU", "GPU"\]
- batch\_size: aligned — \[64, 64\]
- precision: aligned — \["FP32", "FP32"\]

**Limitations:** There is only one timing observation per model\. Hardware is a confounder and variance is unavailable\.

**Minimum next check (proposed):** Time both models on the same device at batch 64 and FP32, using the same warmup, synchronization, and repeated\-run protocol\.

**Observable falsifier:** A controlled baseline/method median time ratio below 2\.0 would challenge the claimed twofold speed advantage\.

## C5

Sprout remains accurate under distribution shift\.

[paper:11](evidence/paper.md#line-11)

**Model analysis: unknown**

No distribution\-shift evaluation is supplied\. The absence does not establish that Sprout fails under shift\.

Evidence:

- [paper:27](evidence/paper.md#line-27)

**Limitations:** The claim does not define the shift or what counts as remaining accurate\.

**Minimum next check (proposed):** Predeclare a concrete shift, such as a fixed blur corruption, and an accuracy\-retention threshold; evaluate both clean and shifted MiniShapes test inputs\.

**Observable falsifier:** Retention below the predeclared threshold would challenge the operationalized robustness claim; no threshold or result is asserted here\.

## C6

The in\-distribution accuracy gain over Linear is 2\.5% relative\.

[paper:12](evidence/paper.md#line-12)

**Model analysis: supported_within_scope**

The supplied accuracy aggregates imply a 2\.5% relative increase over Linear in the described in\-distribution setting\.

Evidence:

- [results:2 \{"id": "sprout"\}](evidence/results.md#line-2)
- [results:3 \{"id": "linear"\}](evidence/results.md#line-3)
- [paper:16](evidence/paper.md#line-16)

**Script check**

relative\_change: consistent — computed 2\.500; claimed 2\.5 ± 0\.05 percent relative\. Selected conditions: aligned\.

- [results:2 \[value\] \{"id": "sprout"\}](evidence/results.md#line-2)
- [results:3 \[value\] \{"id": "linear"\}](evidence/results.md#line-3)
- dataset: aligned — \["MiniShapes", "MiniShapes"\]
- split: aligned — \["test", "test"\]
- metric: aligned — \["accuracy", "accuracy"\]
- unit: aligned — \["percent", "percent"\]
- protocol: aligned — \["fixed\-v1", "fixed\-v1"\]
- budget: aligned — \["10 epochs", "10 epochs"\]
- seeds: aligned — \["11\|22\|33", "11\|22\|33"\]
- aggregation: aligned — \["mean", "mean"\]

**Limitations:** This relative arithmetic does not establish statistical significance or generalization\.

**Minimum next check (proposed):** Recompute both means from the original per\-seed logs, preserving the same split and protocol\.

**Observable falsifier:** A recomputed relative increase outside 2\.5 \+/\- 0\.05 percent would conflict with the rounded claim\.

## Source inventory

Snapshots preserve the reviewed evidence. Hashes identify exact input bytes; they do not prove authenticity.

- [paper](evidence/paper.md): paper\.md — SHA-256 `b4025f859bda98e3ee0c90077f248481fabd5b6fe28c4eb7190d57ff223ae43d`
- [results](evidence/results.md): results\.csv — SHA-256 `02aa99aa74b7e2564a29d1b1e4c22e560ece2cf92c9face1f2a92d2214c71d65`
- [runtime](evidence/runtime.md): runtime\.json — SHA-256 `0b5ddefa6641e019ad22c45028774cf2c3a0e9861a2337c40bf2d88d2c679b6b`
