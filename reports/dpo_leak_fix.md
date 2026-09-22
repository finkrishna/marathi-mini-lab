# DPO leak fix

`DPO-0011` used the same prompt as eval item `MBL-0010` (the doctor-dosage sentence). `DPO-0013` shared a long prefix with `MBL-0009` (the monsoon sentence). Both prompts were replaced before any training.

- `DPO-0011` is now a formal request for a school-fee receipt.
- `DPO-0013` is now a winter-exam timetable sentence. It does not mention the monsoon or June.

`python3 scripts/check_train_eval_overlap.py` exits 0 after the change. The new Marathi lines are still non-gold. A native speaker has not signed off.
