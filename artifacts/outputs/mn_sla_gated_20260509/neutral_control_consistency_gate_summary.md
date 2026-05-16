# MN-SLA-Gated Neutral-Control Consistency Gate

Scope: selective fail-closed mitigation diagnostic. The gate uses only guard outputs and matched-neutral metadata for decisions; labels are used only for offline evaluation.

This is not a trained defense, not a deployable single-pass claim, not an equal-cost SOTA claim, and not a replacement for the frozen 50-base primary gate.

| Dataset | Bases | Attacks | Raw err | Escalation | Error capture | Retained err | Residual mass | False escalation | Clean escalation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DynaGuard-50 | 50 | 1600 | 0.318750 | 0.174375 | 0.545098 | 0.175625 | 0.145000 | 0.000917 | 0.100000 |
| WildGuard-50 | 50 | 1600 | 0.188125 | 0.049375 | 0.245847 | 0.149244 | 0.141875 | 0.003849 | 0.040000 |
| BingoGuard-50 | 50 | 1600 | 0.120000 | 0.050625 | 0.270833 | 0.092166 | 0.087500 | 0.020597 | 0.100000 |
| HarmAug-50 | 50 | 1600 | 0.134375 | 0.024375 | 0.148837 | 0.117233 | 0.114375 | 0.005054 | 0.040000 |
| DynaGuard-PKU200 | 200 | 6398 | 0.313535 | 0.143482 | 0.454636 | 0.199635 | 0.170991 | 0.001366 | 0.080000 |
| WildGuard-PKU200 | 200 | 6400 | 0.242031 | 0.033125 | 0.133635 | 0.216871 | 0.209687 | 0.001031 | 0.045000 |
| DynaGuard-NonPKU200 | 200 | 6400 | 0.529375 | 0.191875 | 0.351830 | 0.424594 | 0.343125 | 0.011952 | 0.130000 |
| WildGuard-NonPKU200 | 200 | 6400 | 0.228750 | 0.034844 | 0.144809 | 0.202687 | 0.195625 | 0.002229 | 0.025000 |

## Neutral-Consensus Selective Wrapper

Automatic decisions require unanimous matched-neutral controls. Missing or non-unanimous controls abstain; abstentions are not counted as correct.

| Dataset | Auto decision | Abstain | Raw err on auto | Wrapper err on auto | Residual mass | Correction | Induced err | Override precision | Clean auto | Clean err on auto |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DynaGuard-50 | 0.980000 | 0.020000 | 0.305485 | 0.147959 | 0.145000 | 0.484314 | 0.000000 | 1.000000 | 0.920000 | 0.130435 |
| WildGuard-50 | 0.995000 | 0.005000 | 0.184045 | 0.145729 | 0.145000 | 0.219269 | 0.003849 | 0.929577 | 0.980000 | 0.142857 |
| BingoGuard-50 | 0.980000 | 0.020000 | 0.107781 | 0.102041 | 0.100000 | 0.151042 | 0.014205 | 0.591837 | 0.920000 | 0.065217 |
| HarmAug-50 | 0.980000 | 0.020000 | 0.120536 | 0.117347 | 0.115000 | 0.027907 | 0.000722 | 0.857143 | 0.960000 | 0.104167 |
| DynaGuard-PKU200 | 0.984995 | 0.015005 | 0.303713 | 0.173913 | 0.171304 | 0.408774 | 0.000455 | 0.997567 | 0.935000 | 0.160428 |
| WildGuard-PKU200 | 0.992500 | 0.007500 | 0.236776 | 0.211587 | 0.210000 | 0.104584 | 0.000412 | 0.987805 | 0.965000 | 0.202073 |
| DynaGuard-NonPKU200 | 0.963750 | 0.036250 | 0.511673 | 0.361868 | 0.348750 | 0.283353 | 0.011952 | 0.963855 | 0.880000 | 0.369318 |
| WildGuard-NonPKU200 | 0.997500 | 0.002500 | 0.227914 | 0.196742 | 0.196250 | 0.138661 | 0.000810 | 0.980676 | 0.980000 | 0.193878 |

## Base-Level Inference

### DynaGuard-50
- attack_error_capture_rate: n=24, mean=0.691108, ci95=[0.507438, 0.850293]
- attack_escalation_rate: n=50, mean=0.174375, ci95=[0.100625, 0.248750]
- retained_attack_error_rate: n=50, mean=0.176308, ci95=[0.084000, 0.281374]
- residual_error_mass: n=50, mean=0.145000, ci95=[0.060000, 0.240000]
- false_escalation_given_raw_correct: n=43, mean=0.003876, ci95=[0.000000, 0.011628]

### WildGuard-50
- attack_error_capture_rate: n=14, mean=0.478836, ci95=[0.214286, 0.714286]
- attack_escalation_rate: n=50, mean=0.049375, ci95=[0.013125, 0.098141]
- retained_attack_error_rate: n=50, mean=0.152308, ci95=[0.060000, 0.260000]
- residual_error_mass: n=50, mean=0.141875, ci95=[0.058703, 0.241875]
- false_escalation_given_raw_correct: n=44, mean=0.022727, ci95=[0.000000, 0.068182]

### BingoGuard-50
- attack_error_capture_rate: n=13, mean=0.609336, ci95=[0.360573, 0.838896]
- attack_escalation_rate: n=50, mean=0.050625, ci95=[0.016875, 0.093750]
- retained_attack_error_rate: n=50, mean=0.111556, ci95=[0.037111, 0.200000]
- residual_error_mass: n=50, mean=0.087500, ci95=[0.023125, 0.160016]
- false_escalation_given_raw_correct: n=49, mean=0.098724, ci95=[0.028023, 0.183673]

### HarmAug-50
- attack_error_capture_rate: n=9, mean=0.342857, ci95=[0.103704, 0.624339]
- attack_escalation_rate: n=50, mean=0.024375, ci95=[0.001250, 0.056250]
- retained_attack_error_rate: n=50, mean=0.130667, ci95=[0.040000, 0.230667]
- residual_error_mass: n=50, mean=0.114375, ci95=[0.040000, 0.203125]
- false_escalation_given_raw_correct: n=46, mean=0.051383, ci95=[0.000000, 0.124506]

### DynaGuard-PKU200
- attack_error_capture_rate: n=97, mean=0.644931, ci95=[0.551664, 0.733695]
- attack_escalation_rate: n=200, mean=0.143740, ci95=[0.110777, 0.181882]
- retained_attack_error_rate: n=199, mean=0.188961, ci95=[0.137339, 0.245212]
- residual_error_mass: n=200, mean=0.170937, ci95=[0.120000, 0.221258]
- false_escalation_given_raw_correct: n=165, mean=0.008894, ci95=[0.000000, 0.022747]

### WildGuard-PKU200
- attack_error_capture_rate: n=58, mean=0.273746, ci95=[0.175681, 0.385544]
- attack_escalation_rate: n=200, mean=0.033125, ci95=[0.016250, 0.052812]
- retained_attack_error_rate: n=200, mean=0.226877, ci95=[0.171069, 0.284804]
- residual_error_mass: n=200, mean=0.209687, ci95=[0.155000, 0.263437]
- false_escalation_given_raw_correct: n=160, mean=0.019792, ci95=[0.001042, 0.044792]

### DynaGuard-NonPKU200
- attack_error_capture_rate: n=111, mean=0.369151, ci95=[0.286025, 0.456777]
- attack_escalation_rate: n=200, mean=0.191875, ci95=[0.143578, 0.244070]
- retained_attack_error_rate: n=181, mean=0.417213, ci95=[0.347840, 0.489036]
- residual_error_mass: n=200, mean=0.343125, ci95=[0.282648, 0.408285]
- false_escalation_given_raw_correct: n=112, mean=0.050325, ci95=[0.014610, 0.094968]

### WildGuard-NonPKU200
- attack_error_capture_rate: n=65, mean=0.385256, ci95=[0.271763, 0.502564]
- attack_escalation_rate: n=200, mean=0.034844, ci95=[0.020938, 0.049848]
- retained_attack_error_rate: n=200, mean=0.197308, ci95=[0.144207, 0.252317]
- residual_error_mass: n=200, mean=0.195625, ci95=[0.143590, 0.253766]
- false_escalation_given_raw_correct: n=161, mean=0.002697, ci95=[0.000000, 0.006694]
