# Data Reconciliation Report
**Date: April 16, 2026**

---

## Issue Identified

Inconsistent accuracy numbers across multiple documents caused by mixing:
1. **ACTUAL baseline results** from master_results.csv
2. **SIMULATED robustness estimates** from CALCULATIONS_SUMMARY.md

---

## Authoritative Source

**PUBLICATION_METRICS.json** - Generated from actual master_results.csv data

All manuscript writing and tables must reference these ONLY:

### Overall Metrics
- **Total LLM Calls**: 2,200
- **Total Scenario Runs**: 1,020
- **Overall Accuracy**: 58.7%
- **Failure Rate**: 48.3% (1,062 failures at <60% accuracy)
- **Collision Rate**: 34.4%

### Provider Accuracy (Across All Modes)
| Provider | Accuracy |
|----------|----------|
| OpenAI   | 60.4%    |
| DeepSeek | 59.5%    |
| Claude   | 56.2%    |

### Mode Accuracy (Across All Providers)
| Mode            | Accuracy |
|-----------------|----------|
| Natural         | 71.3%    |
| Prompt History  | 61.7%    |
| Standard        | 55.8%    |

---

## Removed Documents

**DELETED: CALCULATIONS_SUMMARY.md**
- Reason: Contained simulated robustness degradation values, not actual baseline results
- Values were estimated (e.g., "OpenAI+natural: 78.3%") not measured
- Caused confusion with different numbers in different documents

---

## Inconsistencies Resolved

### Before (Conflicting)
```
PUBLICATION_METRICS.json:    "natural_mode: 71.3%"
CALCULATIONS_SUMMARY.md:     "OpenAI + natural: 78.3%"
ACADEMIC_TABLES_READY.md:    "OpenAI+Vision: 71.3%"
Failure rate documented as:  "25.4% (683/2200)" vs "48.3% (1062/2200)"
```

### After (Authoritative)
```
PUBLICATION_METRICS.json:    "natural_mode: 71.3%"
                             "failure_rate: 48.3% (1062/2200)"
ACADEMIC_TABLES_READY.md:    [SHOULD MATCH - verify alignment]
```

---

## For Manuscript Writing

**Use only:**
1. `PUBLICATION_METRICS.json` - Baseline accuracy numbers
2. `ACADEMIC_TABLES_READY.md` - Formatted tables (verify they match PUBLICATION_METRICS)
3. `robustness_noise_results.csv` - For robustness section (degradation under noise)
4. `robustness_delay_results.csv` - For robustness section (degradation under latency)
5. `failures_categorized.csv` - For failure analysis section

**Do NOT use:**
- ❌ CALCULATIONS_SUMMARY.md (DELETED - had simulated data)
- ❌ Any numbers that don't appear in PUBLICATION_METRICS.json

---

## Next Steps

1. ✅ Remove CALCULATIONS_SUMMARY.md from git
2. ✅ Document authoritative metrics (this file)
3. ⏳ Verify ACADEMIC_TABLES_READY.md matches PUBLICATION_METRICS.json
4. ⏳ Begin manuscript writing with consistent baselines
