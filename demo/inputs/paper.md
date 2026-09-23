# Sprout: A Tiny Classification Study

This is an original fictional teaching example, not a published paper or an experimental result.

## Abstract

Sprout improves classification accuracy across all image datasets and compute budgets.
On MiniShapes test data under the fixed 10-epoch protocol, Sprout reaches 82.0% accuracy.
Under that protocol, Sprout exceeds Linear by 5.0 percentage points.
Under identical hardware and batch settings, Sprout is 2.0 times faster than Linear.
Sprout remains accurate under distribution shift.
The in-distribution accuracy gain over Linear is 2.5% relative.

## Experiment

The only accuracy experiment uses MiniShapes, the test split, and 10 training epochs.
Both models use three seeds (11, 22, 33); results.csv contains their unweighted mean accuracies on a 0-100 scale.
The accuracy protocol is fixed-v1. No confidence interval or significance test is supplied.

## Timing

runtime.json records one timing observation per model; preprocessing time is excluded.
Sprout was timed on a GPU and Linear on a CPU, both at batch size 64 and FP32.

## Limitations

No other dataset, compute budget, or distribution-shift evaluation is included in these materials.
