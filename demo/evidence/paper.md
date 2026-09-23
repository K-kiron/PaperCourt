# paper\.md

SHA-256: `b4025f859bda98e3ee0c90077f248481fabd5b6fe28c4eb7190d57ff223ae43d`

[Original bytes](../inputs/paper.md)

## Line 1

    # Sprout: A Tiny Classification Study

## Line 2



## Line 3

    This is an original fictional teaching example, not a published paper or an experimental result.

## Line 4



## Line 5

    ## Abstract

## Line 6



## Line 7

    Sprout improves classification accuracy across all image datasets and compute budgets.

## Line 8

    On MiniShapes test data under the fixed 10-epoch protocol, Sprout reaches 82.0% accuracy.

## Line 9

    Under that protocol, Sprout exceeds Linear by 5.0 percentage points.

## Line 10

    Under identical hardware and batch settings, Sprout is 2.0 times faster than Linear.

## Line 11

    Sprout remains accurate under distribution shift.

## Line 12

    The in-distribution accuracy gain over Linear is 2.5% relative.

## Line 13



## Line 14

    ## Experiment

## Line 15



## Line 16

    The only accuracy experiment uses MiniShapes, the test split, and 10 training epochs.

## Line 17

    Both models use three seeds (11, 22, 33); results.csv contains their unweighted mean accuracies on a 0-100 scale.

## Line 18

    The accuracy protocol is fixed-v1. No confidence interval or significance test is supplied.

## Line 19



## Line 20

    ## Timing

## Line 21



## Line 22

    runtime.json records one timing observation per model; preprocessing time is excluded.

## Line 23

    Sprout was timed on a GPU and Linear on a CPU, both at batch size 64 and FP32.

## Line 24



## Line 25

    ## Limitations

## Line 26



## Line 27

    No other dataset, compute budget, or distribution-shift evaluation is included in these materials.
