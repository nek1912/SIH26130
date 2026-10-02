# Maharashtra Active Rule Regulatory Evidence Integrity Audit

**Document Reference**: `docs/audits/audit_mh_active_rule_evidence_integrity.md`  
**Date**: 2026-09-29  
**Auditor**: Antigravity Regulatory Audit Agent  
**Jurisdiction**: `IN-MH` (Maharashtra Industrial Approvals Pack)  
**Baseline Verification**:
- `DEFAULT_JURISDICTION = "IN-GJ"` (constant; IN-MH isolated and non-default)
- Active Maharashtra approval rules: **26**
- Deferred Maharashtra approval rules: **61** (`MH_DEFERRED_RULES`)
- Requires-confirmation rules: **26**
- Do-not-implement rules: **3**
- Unknown status rules: **3**
- Registered Maharashtra facts: **128** (`MH_FACTS` in `backend/app/rules/facts.py`)
- Authoritative reference dataset: `UdyamDwaar MH Chemical Pack – report + 18 CSVs (4)/csv/rule_register_v5.csv`
- Production modifications made: **ZERO** (Strict audit-only policy)

---

## 1. Executive Summary

This audit constitutes the exhaustive evidence integrity verification of all **26 active rules** currently encoded in the Maharashtra regulatory pack (`backend/app/seed/mh/approvals.py`). The objective is to verify whether each active rule is genuinely backed by primary statutory evidence, whether its mathematical and logical predicates faithfully represent the underlying legal provisions, whether its sources and locators are valid and verified, whether its authority routing is legally supported, and whether any semantic overstatement or inversion exists.

### Summary Classification of Active Rules

| Classification | Count | Rule IDs | Summary Rationale |
| :--- | :---: | :--- | :--- |
| **SAFE** | **15** | `R-002`, `R-007`, `R-009`, `R-011`, `R-012`, `R-018`, `R-026`, `R-028`, `R-043`, `R-044`, `R-056`, `R-073`, `R-086`, `R-089`, `R-096` | Fully grounded in T1/T2 primary statutory evidence; predicates accurately match legal texts; facts exist in `MH_FACTS`; semantic roles are faithful. |
| **NEEDS_REVIEW** | **6** | `R-046`, `R-067`, `R-070`, `R-084`, `R-093`, `R-094` | Evidence is genuine and rules operate safely in runtime, but documentary gaps exist: missing specific clause locators (`R-046`), year-only dates (`R-067`, `R-093`), unresolved MH State licensing officer identity (`R-067`), or compliance duties/location triggers mapped to empty authority strings (`R-070`, `R-084`, `R-093`, `R-094`). |
| **BLOCKING** | **5** | `R-030`, `R-035`, `R-077`, `R-083`, `R-087` | Significant semantic inversion, legal contradiction, or regulatory overstatement that requires architectural migration or deferral before full production cutover. |

---

## 2. Master Verification Matrix (All 26 Active Rules)

| rule_id | approval_id | Predicate Summary | Fact IDs | Source ID | Source Type | Provision / Locator | Effective Date | Authority | Status in Register | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `R-002` | `APR-001` | `F-PRC-01 < 25 AND F-PRC-02 < 25 AND F-PRC-03 == False` | `F-PRC-01`, `F-PRC-02`, `F-PRC-03` | `SRC-001` | OFFICIAL_PRIMARY | Item 5(f) col 5; footnote 76 | `2014-06-25` | `AUT-001 / AUT-002` | SAFE | **SAFE** |
| `R-007` | `APR-003` | `F-BLD-01 >= 20000 AND F-BLD-01 < 150000` | `F-BLD-01` | `SRC-001`, `SRC-179` | OFFICIAL_PRIMARY | Item 8(a) | `2006-09-14` | `AUT-002` | SAFE | **SAFE** |
| `R-009` | `APR-004` | `F-BLD-03 >= 50 OR F-BLD-01 >= 150000` | `F-BLD-01`, `F-BLD-03` | `SRC-001` | OFFICIAL_PRIMARY | Item 8(b) | `2006-09-14` | `AUT-002` | SAFE | **SAFE** |
| `R-011` | `APR-006` | `F-PRD-02 IN ['PESTICIDE_TECHNICAL']` | `F-PRD-02` | `SRC-001` | OFFICIAL_PRIMARY | Item 5(b) | `2006-09-14` | `AUT-001` | SAFE | **SAFE** |
| `R-012` | `APR-007` | `F-PRD-02 IN ['PAINT_INTEGRATED']` | `F-PRD-02` | `SRC-001` | OFFICIAL_PRIMARY | Item 5(h) | `2006-09-14` | `AUT-002` | SAFE | **SAFE** |
| `R-018` | `APR-010` | `F-HW-01 == True` | `F-HW-01` | `SRC-013` | CENTRAL_RULES | Rule 6(1) | `2016-04-04` | `AUT-003` | SAFE | **SAFE** |
| `R-026` | `APR-019` | `F-LAB-03 >= 50 AND F-LAB-09 == False` | `F-LAB-03`, `F-LAB-09` | `SRC-081`, `SRC-026` | OFFICIAL_PRIMARY | OSH Code s.45(2) | `2025-11-21` | `AUT-006` | SAFE | **SAFE** |
| `R-028` | `APR-023` | `F-BLR-04==True AND F-BLR-01>=25 AND NOT(F-BLR-05<1 AND F-BLR-02<1) AND NOT(F-BLR-03<100)` | `F-BLR-01`, `F-BLR-02`, `F-BLR-03`, `F-BLR-04`, `F-BLR-05` | `SRC-034` | OFFICIAL_PRIMARY | Boilers Act 2025 s.2(c) | `2025-05-01` | `AUT-007` | SAFE | **SAFE** |
| `R-030` | `APR-026` | `F-PET-01 == 'B' AND F-PET-02 <= 2500 AND F-PET-04 <= 1000` | `F-PET-01`, `F-PET-02`, `F-PET-04` | `SRC-092`, `SRC-017` | OFFICIAL_PRIMARY | Petroleum Act s.7(i) | None (`2002`) | `AUT-008 / AUT-009` | SAFE | **BLOCKING** |
| `R-035` | `APR-029` | `F-LOC-01 == True` | `F-LOC-01` | `SRC-043` | OFFICIAL_PORTAL (T3) | `-` | None (`-`) | `AUT-010` | SAFE | **BLOCKING** |
| `R-043` | `APR-043` | `F-INC-01 IN ['MICRO', 'SMALL'] AND F-WAT-05 < 10` | `F-INC-01`, `F-WAT-05` | `SRC-052` | OFFICIAL_PRIMARY | Exemptions list para 1.0(v) | `2020-09-24` | `AUT-013` | SAFE | **SAFE** |
| `R-044` | `APR-043` | `F-WAT-06 == 'DOMESTIC_ONLY' AND F-WAT-05 <= 5` | `F-WAT-05`, `F-WAT-06` | `SRC-052` | OFFICIAL_PRIMARY | Exemptions list para 1.0(vi) | `2020-09-24` | `AUT-013` | SAFE | **SAFE** |
| `R-046` | `APR-044` | `F-WAT-08 == True` | `F-WAT-08` | `SRC-052` | OFFICIAL_PRIMARY | `-` | `2020-09-24` | `AUT-013` | SAFE | **NEEDS_REVIEW** |
| `R-056` | `APR-054` | `F-HW-03 == True` | `F-HW-03` | `SRC-013` | CENTRAL_RULES | Rule 9 | None (`2016`) | `AUT-003` | SAFE | **SAFE** |
| `R-067` | `APR-055` | `F-INS-01 == True` | `F-INS-01` | `SRC-100` | OFFICIAL_PRIMARY | s.13 | None (`1968`) | Licensing officer (State) | SAFE | **NEEDS_REVIEW** |
| `R-070` | `CMP-018` | `(F-LAB-07==False AND F-LAB-01>=500) OR (F-LAB-07==True AND F-LAB-01>=250)` | `F-LAB-01`, `F-LAB-07` | `SRC-081` | OFFICIAL_PRIMARY | s.22(2) | `2025-11-21` | `""` (`-`) | SAFE | **NEEDS_REVIEW** |
| `R-073` | `APR-023` | `F-BLR-06 > 1000` | `F-BLR-06` | `SRC-085` | OFFICIAL_PRIMARY | BOE rule | `2025-09-23` | `AUT-007` | SAFE | **SAFE** |
| `R-077` | `APR-043` | `F-GW-01 == 'OVER_EXPLOITED' AND ((F-EXP-01 == False AND F-INC-01 NOT IN ['MICRO','SMALL','MEDIUM']) OR F-EXP-01 == True)` | `F-GW-01`, `F-EXP-01`, `F-INC-01` | `SRC-052` | OFFICIAL_PRIMARY | para 4.1 | `2020-09-24` | `AUT-013` | SAFE | **BLOCKING** |
| `R-083` | `LOC-CRZ` | `F-GEO-01 IN ['CRZ-I', 'CRZ-II', 'CRZ-III', 'CRZ-IV']` | `F-GEO-01` | `SRC-112` | NOTIFICATION | paras 4(i), 4(ii), 4(xi) | `2019-01-18` | `MCZMA / MoEFCC` | SAFE | **BLOCKING** |
| `R-084` | `LOC-FOREST` | `F-LOC-15 == True` | `F-LOC-15` | `SRC-113` | CENTRAL_RULES | r.9, r.10 | `2023-12-01` | `MoEFCC / RO / Forest Dept` | SAFE | **NEEDS_REVIEW** |
| `R-086` | `APR-023` | `R-028 tree AND F-BLR-07 == 'NOT_REGISTERED'` | `F-BLR-01..05`, `F-BLR-07` | `SRC-034` | OFFICIAL_PRIMARY | s.12(1)-(6) | `2025-05-01` | `AUT-007` | SAFE | **SAFE** |
| `R-087` | `APR-023` | `F-BLR-07 == 'REGISTERED_UNDER_1923_ACT'` | `F-BLR-07` | `SRC-034` | OFFICIAL_PRIMARY | s.45(2) | `2025-05-01` | `AUT-007` | SAFE | **BLOCKING** |
| `R-089` | `APR-022` | `F-LAB-08 >= 10` | `F-LAB-08` | `SRC-081` | OFFICIAL_PRIMARY | s.59 | `2025-11-21` | `AUT-006` | SAFE | **SAFE** |
| `R-093` | `CMP-024` | `F-TRN-01 == True` | `F-TRN-01` | `SRC-102` | CENTRAL_RULES | r.131 | None (`1993`) | `""` (`-`) | SAFE | **NEEDS_REVIEW** |
| `R-094` | `CMP-025` | `F-EEE-01 >= 1000` | `F-EEE-01` | `SRC-135` | CENTRAL_RULES | r.3; r.8 | `2023-04-01` | `""` (`-`) | SAFE | **NEEDS_REVIEW** |
| `R-096` | `APR-010` | `F-HW-04 IN ['CLASS_A', 'CLASS_B', ...]` | `F-HW-04` | `SRC-120` | CENTRAL_RULES (T2) | Schedule II Class A/B/C | `2016-04-04` | `AUT-003` | SAFE | **SAFE** |

---

## 3. Systematic Audit by the Eight Required Dimensions

### 3.1. Active Rule with Missing Source
- **Audit Requirement**: Identify active rules lacking an official source citation or grounded locator.
- **Findings**:
  1. `R-035` (`APR-029`): Cites `SRC-043` (`MIDC Single Window Portal / Circulars`), a Tier-3 portal source. In both `rule_register_v5.csv` and the Python codebase, the locator is `"-"` (no regulation, circular number, or section locator is given).
  2. `R-046` (`APR-044`): Cites `SRC-052` (`CGWA Guidelines 2020`), but the citation locator is `"-"` (no specific paragraph or clause is cited).
- **Classification**:
  - `R-035`: **BLOCKING** (conflates branch guard with statutory plot allotment without primary legal source).
  - `R-046`: **NEEDS_REVIEW** (the source `SRC-052` is valid T1; only the clause locator is blank).

### 3.2. Active Rule with Unsupported Predicate
- **Audit Requirement**: Identify active rules whose conditions use unsupported engine operations or deviate from the registered statutory predicate.
- **Findings**:
  1. `R-030` (`APR-026`): Register lists `required_inputs` as `F-PET-01;F-PET-02;F-PET-03;F-PET-04`. In code, only `F-PET-01`, `F-PET-02`, and `F-PET-04` are evaluated. `F-PET-03` (individual receptacle capacity) is omitted because `F-PET-04` (maximum receptacle capacity) functionally bounds the condition (`<= 1000 L`). While mathematically sound, it is a slight divergence from the register.
  2. `R-084` (`LOC-FOREST`): Register lists `required_inputs` as `F-LOC-15;F-GEO-03`. The code predicate evaluates solely `F-LOC-15 == True`, omitting `F-GEO-03` (forest land area in hectares). The area determines whether Central approval is via the Regional Empowered Committee (`<= 40 ha`) or Central Government (`> 40 ha`), which is authority routing rather than approval applicability.
  3. `R-086` (`APR-023`): Register condition references `R-028 == TRUE AND NOT registered`. Because the engine lacks cross-rule references, `R-086` explicitly inlines the 4-conjunct tree of `R-028`. Verified safe and synchronized by unit tests.
  4. `R-087` (`APR-023`): Register lists `F-BLR-07;F-BLR-08`. Code evaluates only `F-BLR-07 == 'REGISTERED_UNDER_1923_ACT'`, omitting `F-BLR-08` (certificate expiry date), which is an ongoing compliance tracking date, not applicability.
- **Classification**:
  - `R-086`, `R-084`, `R-087`: **SAFE** to **NEEDS_REVIEW** on predicate structure.

### 3.3. Active Rule with Missing Effective Date
- **Audit Requirement**: Identify active rules where `effective_from` is `None` or missing.
- **Findings**:
  1. `R-030` (`APR-026`): `effective_from` is `None`. Register states `2002` (year-only, Petroleum Rules 2002).
  2. `R-035` (`APR-029`): `effective_from` is `None`. Register states `"-"` (no date established).
  3. `R-056` (`APR-054`): `effective_from` is `None`. Register states `2016` (year-only, HOWM Rules 2016).
  4. `R-067` (`APR-055`): `effective_from` is `None`. Register states `1968` (year-only, Insecticides Act 1968).
  5. `R-093` (`CMP-024`): `effective_from` is `None`. Register states `1993` (year-only, CMVR Amendment 1993).
- **Classification**:
  - `R-056`, `R-067`, `R-093`: **NEEDS_REVIEW** (omitting the exact day/month to avoid inventing precision is compliant with RULE 1 of `RULES.md`, but requires documentation).
  - `R-035`: **BLOCKING** (missing both date and primary locator).

### 3.4. Active Rule Using an Unregistered Fact
- **Audit Requirement**: Verify that every fact field referenced by any active rule exists in `MH_FACTS`.
- **Findings**:
  - **ZERO unregistered facts detected**.
  - All fact IDs referenced across all 26 active rules (`F-PRC-01..03`, `F-BLD-01`, `F-BLD-03`, `F-PRD-02`, `F-HW-01`, `F-HW-03`, `F-HW-04`, `F-LAB-01`, `F-LAB-03`, `F-LAB-07`, `F-LAB-08`, `F-LAB-09`, `F-BLR-01..07`, `F-PET-01..02`, `F-PET-04`, `F-LOC-01`, `F-LOC-15`, `F-INC-01`, `F-WAT-05`, `F-WAT-06`, `F-WAT-08`, `F-GW-01`, `F-EXP-01`, `F-GEO-01`, `F-TRN-01`, `F-EEE-01`) have complete `FactSpec` entries in `backend/app/rules/facts.py` with validated data types and enum bounds.
- **Classification**: **SAFE**.

### 3.5. Active Rule Using Gujarat-Specific Data
- **Audit Requirement**: Verify that no active Maharashtra rule references Gujarat fields, approvals, or data.
- **Findings**:
  - **ZERO Gujarat leaks detected**.
  - No legacy Gujarat field from `validation.ALLOWED_FIELDS` is present in any active MH rule.
  - All approval IDs adhere to Maharashtra v5 designations (`APR-001` through `APR-055`, `CMP-*`, `LOC-*`), completely segregated from the Gujarat `A01`–`A10` catalogue.
- **Classification**: **SAFE**.

### 3.6. Active Rule Whose Authority is Unsupported
- **Audit Requirement**: Verify that the authority mapped to each active rule is supported by the official register and legal sources.
- **Findings**:
  1. `R-067` (`APR-055`): Code maps authority as `"Licensing officer (State; identity in MH UNKNOWN)"`. Register lists `authority: "-"`. While Section 13 of the Insecticides Act 1968 mandates licensing by the State Government, the specific designation in Maharashtra (e.g., Commissioner of Agriculture) is unconfirmed.
  2. `R-070` (`CMP-018`), `R-093` (`CMP-024`), `R-094` (`CMP-025`): Register lists authority as `"-"`, and code maps authority to `""`. These are compliance/operational duties under the OSH Code, CMVR, and E-Waste Rules; they have no single issuing authority because they are continuous duties, not clearance applications.
  3. `R-083` (`LOC-CRZ`): Register lists authority as `"-"`. Code maps authority to `"MCZMA / MoEFCC"`. Grounded in CRZ Notification 2019 (Maharashtra Coastal Zone Management Authority).
  4. `R-084` (`LOC-FOREST`): Register lists authority as `"-"`. Code maps authority to `"MoEFCC / Regional Office / State Forest Dept"`. Grounded in Van Rules 2023.
- **Classification**: **NEEDS_REVIEW** (for `R-067`, `R-070`, `R-093`, `R-094`).

### 3.7. Active Rule Whose Wording Overstates the Evidence
- **Audit Requirement**: Identify rules whose operational behavior overstates statutory evidence or presents exemptions/prohibitions as affirmative permits.
- **Findings**:
  1. `R-030` (`APR-026`): **Severe Inversion**. Section 7(i) of the Petroleum Act 1934 provides a statutory exemption: no licence is required for Class B petroleum <= 2500 L in receptacles <= 1000 L. However, `R-030` is currently encoded with role `TRIGGER` on `APR-026`. If an applicant meets the condition, the engine asserts that Petroleum Licence `APR-026` **APPLIES**, directly contradicting the statute.
  2. `R-087` (`APR-023`): **Severe Inversion**. Section 45(2)(f) of the Boilers Act 2025 states that boilers registered under the 1923 Act are deemed registered under the new Act. Encoded with role `TRIGGER`, `R-087` evaluates to `APPLIES`, falsely requiring the applicant to seek fresh registration under Section 12(1).
  3. `R-077` (`APR-043`): **Prohibition Conflated with Permit**. Para 4.1 of the CGWA 2020 Guidelines explicitly bars the grant of an NOC to new non-MSME industries or expanding industries in Over-Exploited areas. Encoded as a `TRIGGER` on `APR-043`, it evaluates to `APPLIES`, falsely signalling to an industrial proponent that they can apply for and obtain an abstraction NOC in a prohibited zone.
  4. `R-083` (`LOC-CRZ`): **Prohibition Conflated with Permit**. Para 4(i) of the CRZ Notification 2019 prohibits the establishment or expansion of chemical industries within CRZ. Presenting `LOC-CRZ` as an applicable approval clearance mischaracterizes a blanket environmental prohibition.
  5. `R-035` (`APR-029`): **Routing Conflated with Permit**. Automatically triggers `APR-029` (MIDC Plot Allotment) for any project in an MIDC area (`F-LOC-01 == True`), ignoring whether the applicant already owns or leases an existing industrial plot.
  6. `R-070`, `R-093`, `R-094`: **Compliance Duties Conflated with Approvals**. Operating requirements (appointing a safety officer, following transport placard rules, handing over e-waste) are represented as `ApprovalRule` objects, which conflates operational compliance with pre-establishment / pre-operation clearances.
- **Classification**:
  - `R-030`, `R-087`, `R-077`, `R-083`, `R-035`: **BLOCKING**.
  - `R-070`, `R-093`, `R-094`: **NEEDS_REVIEW**.

### 3.8. Active Rule That Should Actually Be Deferred
- **Audit Requirement**: Identify active rules that should be deferred to preserve regulatory accuracy.
- **Findings**:
  1. `R-030`: Must be migrated to `Role.EXEMPTION` under an explicit approval composition on `APR-026` (as already planned in `PRD.md`), or deferred until such composition is implemented. Currently, running it as a trigger produces illegal output.
  2. `R-087`: Must be migrated to `Role.EXEMPTION` / deemed status under `APR-023`, or deferred.
  3. `R-077`: Must be split into an explicit prohibition / blocker or deferred from returning `APPLIES`.
  4. `R-035`: Should be deferred or refactored into a location property rather than an approval applicability rule.
  5. `R-083`: Should be deferred from the approval catalogue and surfaced as a statutory siting prohibition.
- **Classification**: **BLOCKING**.

---

## 4. In-Depth Technical Dossier by Rule

### Rule `R-002`: Small-Unit Classification Facet (`APR-001`)
- **Approval Target**: `APR-001` (Prior Environmental Clearance - Cat A / Cat B)
- **Role**: `RuleRole.CLASSIFICATION`
- **Condition**: `F-PRC-01 < 25 AND F-PRC-02 < 25 AND F-PRC-03 == False`
- **Source**: `SRC-001`, Item 5(f) column 5 (Footnote 76, inserted by S.O. 1223(E) dated 27-03-2020)
- **Effective Date**: `2014-06-25`
- **Authority**: `AUT-001 (Cat A) / AUT-002 (Cat B)`
- **Evaluation**: Fully backed by MoEFCC EIA Notification 2006 Item 5(f). Role `CLASSIFICATION` is verified: `R-002` never independently triggers `APR-001`, avoiding false application.
- **Verdict**: **SAFE**.

### Rule `R-007`: EC Category B Built-up Area [20,000, 150,000) m² (`APR-003`)
- **Approval Target**: `APR-003` (Prior EC - Category B Item 8(a))
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-BLD-01 >= 20000 AND F-BLD-01 < 150000`
- **Sources**: `SRC-001`, `SRC-179`, Item 8(a)
- **Effective Date**: `2006-09-14`
- **Authority**: `AUT-002` (SEIAA Maharashtra)
- **Evaluation**: Verbatim statutory thresholds under EIA Notification Item 8(a). Predicate bounds `[20000, 150000)` are exact.
- **Verdict**: **SAFE**.

### Rule `R-009`: EC Category B Townships Area / Built-up (`APR-004`)
- **Approval Target**: `APR-004` (Prior EC - Category B Item 8(b))
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-BLD-03 >= 50 OR F-BLD-01 >= 150000`
- **Source**: `SRC-001`, Item 8(b)
- **Effective Date**: `2006-09-14`
- **Authority**: `AUT-002` (SEIAA Maharashtra)
- **Evaluation**: Verbatim statutory thresholds under EIA Notification Item 8(b) (site area >= 50 ha OR built-up area >= 150,000 m²). Disjunction logic (`OR`) properly preserves three-valued evaluation.
- **Verdict**: **SAFE**.

### Rule `R-011`: Prior EC Item 5(b) Pesticides (`APR-006`)
- **Approval Target**: `APR-006` (Prior EC - Category A Item 5(b))
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-PRD-02 IN ['PESTICIDE_TECHNICAL']`
- **Source**: `SRC-001`, Item 5(b)
- **Effective Date**: `2006-09-14`
- **Authority**: `AUT-001` (MoEFCC)
- **Evaluation**: Item 5(b) mandates that all pesticide technical manufacturing units fall under Category A (MoEFCC appraisal).
- **Verdict**: **SAFE**.

### Rule `R-012`: Prior EC Item 5(h) Integrated Paints (`APR-007`)
- **Approval Target**: `APR-007` (Prior EC - Category B Item 5(h))
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-PRD-02 IN ['PAINT_INTEGRATED']`
- **Source**: `SRC-001`, Item 5(h)
- **Effective Date**: `2006-09-14`
- **Authority**: `AUT-002` (SEIAA Maharashtra)
- **Evaluation**: Item 5(h) mandates Category B appraisal for integrated paint manufacturing units.
- **Verdict**: **SAFE**.

### Rule `R-018`: Hazardous Waste Authorisation on Generation (`APR-010`)
- **Approval Target**: `APR-010` (HOWM Form 1 -> Form 2 Authorisation)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-HW-01 == True`
- **Source**: `SRC-013`, HOWM Rules 2016 Rule 6(1)
- **Effective Date**: `2016-04-04`
- **Authority**: `AUT-003` (MPCB)
- **Evaluation**: Under Rule 6(1) of HOWM Rules 2016, every occupier of a facility generating hazardous or other wastes must obtain an authorisation from the State Pollution Control Board.
- **Verdict**: **SAFE**.

### Rule `R-026`: CLRA Principal Employer Registration (`APR-019`)
- **Approval Target**: `APR-019` (Registration of Principal Employer under Contract Labour)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-LAB-03 >= 50 AND F-LAB-09 == False`
- **Sources**: `SRC-081` (OSH Code 2020), `SRC-026`, Section 45(2)
- **Effective Date**: `2025-11-21`
- **Authority**: `AUT-006` (Labour Commissioner)
- **Evaluation**: OSH Code s.45(2) establishes the threshold of 50 contract workers with an explicit statutory exception for casual or intermittent work (`F-LAB-09 == False`). Fails closed if exception fact is missing.
- **Verdict**: **SAFE**.

### Rule `R-028`: Statutory Boiler Definition (`APR-023`)
- **Approval Target**: `APR-023` (Boiler Registration / Approval)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-BLR-04 == True AND F-BLR-01 >= 25 AND NOT(F-BLR-05 < 1 AND F-BLR-02 < 1) AND NOT(F-BLR-03 < 100)`
- **Source**: `SRC-034`, Boilers Act 2025 Section 2(c)
- **Effective Date**: `2025-05-01`
- **Authority**: `AUT-007` (Directorate of Steam Boilers)
- **Evaluation**: Transcribes the four statutory prongs of Section 2(c) under the newly enacted Boilers Act 2025. Three-valued negation is strictly preserved.
- **Verdict**: **SAFE**.

### Rule `R-030`: Petroleum Class B Exemption (`APR-026`)
- **Approval Target**: `APR-026` (Petroleum Storage Licence / DA NOC)
- **Role**: `RuleRole.TRIGGER` *(Defective staging)*
- **Condition**: `F-PET-01 == 'B' AND F-PET-02 <= 2500 AND F-PET-04 <= 1000`
- **Sources**: `SRC-092` (Petroleum Act 1934 Section 7(i)), `SRC-017` (PESO SOP Exemption Table)
- **Effective Date**: `None` in code (`2002` in register)
- **Authority**: `AUT-008 / AUT-009` (District Magistrate / PESO)
- **Critical Finding**: Section 7(i) of the Petroleum Act 1934 provides an **exemption from licence requirements**. Because `R-030` is currently encoded as `RuleRole.TRIGGER`, satisfying this condition produces `APPLIES` at approval level. This inverts the statutory determination by claiming that a facility qualifying for an exemption is legally required to obtain a licence.
- **Verdict**: **BLOCKING** *(Requires migration to `RuleRole.EXEMPTION` inside `APR-026` composition)*.

### Rule `R-035`: MIDC Branch Guard (`APR-029`)
- **Approval Target**: `APR-029` (MIDC Plot Allotment / Offer Letter)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-LOC-01 == True`
- **Source**: `SRC-043` (T3 Portal: MIDC Single Window Portal), locator `"-"`
- **Effective Date**: `None` in code (`"-"` in register)
- **Authority**: `AUT-010` (MIDC)
- **Critical Finding**: `R-035` is an infrastructure routing guard, not an approval applicability rule. It unconditionally triggers `APR-029` (Plot Allotment) for any enterprise situated in an MIDC estate, without primary statutory evidence or provision locator. Existing factories already in possession of an MIDC plot do not require fresh plot allotment.
- **Verdict**: **BLOCKING**.

### Rule `R-043`: CGWA Ground Water MSE Exemption (`APR-043`)
- **Approval Target**: `APR-043` (CGWA NOC for Ground Water Abstraction)
- **Role**: `RuleRole.EXEMPTION`
- **Condition**: `F-INC-01 IN ['MICRO', 'SMALL'] AND F-WAT-05 < 10`
- **Source**: `SRC-052`, CGWA Guidelines 2020 Exemptions List para 1.0(v)
- **Effective Date**: `2020-09-24`
- **Authority**: `AUT-013` (Central Ground Water Authority)
- **Evaluation**: Successfully migrated to `RuleRole.EXEMPTION` in the P0 exception-semantics architecture. Fulfilling this condition defeats the duty to obtain a CGWA NOC when evaluated under `APR-043` composition.
- **Verdict**: **SAFE**.

### Rule `R-044`: CGWA Ground Water Domestic Exemption (`APR-043`)
- **Approval Target**: `APR-043` (CGWA NOC for Ground Water Abstraction)
- **Role**: `RuleRole.EXEMPTION`
- **Condition**: `F-WAT-06 == 'DOMESTIC_ONLY' AND F-WAT-05 <= 5`
- **Source**: `SRC-052`, CGWA Guidelines 2020 Exemptions List para 1.0(vi)
- **Effective Date**: `2020-09-24`
- **Authority**: `AUT-013` (Central Ground Water Authority)
- **Evaluation**: Successfully migrated to `RuleRole.EXEMPTION` in `docs/audits/audit_mh_r044_exemption_migration.md`. Defeats duty without independently triggering approval.
- **Verdict**: **SAFE**.

### Rule `R-046`: CGWA Dewatering NOC Trigger (`APR-044`)
- **Approval Target**: `APR-044` (CGWA NOC for Dewatering)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-WAT-08 == True`
- **Source**: `SRC-052`, locator `"-"`
- **Effective Date**: `2020-09-24`
- **Authority**: `AUT-013` (CGWA)
- **Evaluation**: Grounded in CGWA Guidelines 2020 requirement that infrastructure dewatering or industrial construction dewatering requires prior permission. The specific guideline clause locator is missing (`"-"`).
- **Verdict**: **NEEDS_REVIEW** *(Grounded in source, but clause locator requires citation enrichment)*.

### Rule `R-056`: Hazardous Waste Utilisation under Rule 9 (`APR-054`)
- **Approval Target**: `APR-054` (HOWM Rule 9 Utilisation Permission)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-HW-03 == True`
- **Source**: `SRC-013`, HOWM Rules 2016 Rule 9
- **Effective Date**: `None` in code (`2016` in register)
- **Authority**: `AUT-003 (CPCB approval if no SOP)`
- **Evaluation**: Verbatim statutory duty under Rule 9 of HOWM Rules 2016. Effective date is year-only in the register.
- **Verdict**: **SAFE**.

### Rule `R-067`: Insecticide Manufacturing Licence (`APR-055`)
- **Approval Target**: `APR-055` (Insecticides Act 1968 Section 13 Licence)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-INS-01 == True`
- **Source**: `SRC-100`, Section 13
- **Effective Date**: `None` in code (`1968` in register)
- **Authority**: `"Licensing officer (State; identity in MH UNKNOWN)"`
- **Evaluation**: Statutory basis in Section 13 of the Insecticides Act 1968 is clear. However, the exact administrative identity of the licensing authority in Maharashtra is not verified, and effective date is year-only.
- **Verdict**: **NEEDS_REVIEW**.

### Rule `R-070`: Safety Officer Headcount Thresholds (`CMP-018`)
- **Approval Target**: `CMP-018` (Appointment of Safety Officer)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `(F-LAB-07 == False AND F-LAB-01 >= 500) OR (F-LAB-07 == True AND F-LAB-01 >= 250)`
- **Source**: `SRC-081`, OSH Code 2020 Section 22(2)
- **Effective Date**: `2025-11-21`
- **Authority**: `""` in code (`"-"` in register)
- **Evaluation**: Accurate mathematical transcription of OSH Code Section 22(2). However, `CMP-018` is an ongoing statutory compliance obligation (`compliance.csv`), not an approval clearance application (`approvals.csv`). It has no issuing authority.
- **Verdict**: **NEEDS_REVIEW** *(Subsystem categorization tension)*.

### Rule `R-073`: Boiler Operation Engineer Requirement (`APR-023`)
- **Approval Target**: `APR-023` (Boiler Operation / Personnel Requirement)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-BLR-06 > 1000`
- **Source**: `SRC-085`, Boiler Operation Engineers' Rules 2025
- **Effective Date**: `2025-09-23`
- **Authority**: `AUT-007` (Directorate of Steam Boilers)
- **Evaluation**: Primary official gazette notification G.S.R. 705(E) dated 22-09-2025. Strictly checks heating surface strictly greater than 1000 m². Linked as an operational personnel condition to `APR-023`.
- **Verdict**: **SAFE**.

### Rule `R-077`: CGWA Over-Exploited Area Abstraction (`APR-043`)
- **Approval Target**: `APR-043` (CGWA NOC for Ground Water Abstraction)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-GW-01 == 'OVER_EXPLOITED' AND ((F-EXP-01 == False AND F-INC-01 NOT IN ['MICRO','SMALL','MEDIUM']) OR F-EXP-01 == True)`
- **Source**: `SRC-052`, CGWA Guidelines 2020 para 4.1
- **Effective Date**: `2020-09-24`
- **Authority**: `AUT-013` (CGWA)
- **Critical Finding**: Para 4.1 of the CGWA Guidelines states that in Over-Exploited assessment units, NOC **shall not be granted** to new industries (other than MSMEs) or existing industries expanding abstraction. Currently encoded as `RuleRole.TRIGGER` on `APR-043`, triggering `APPLIES` when the condition is met. This misleads users into believing an NOC is applicable and obtainable, when in law it is prohibited.
- **Verdict**: **BLOCKING** *(Requires refactoring into a statutory prohibition blocker or composition)*.

### Rule `R-083`: Coastal Regulation Zone Siting Prohibition (`LOC-CRZ`)
- **Approval Target**: `LOC-CRZ` (CRZ Siting Clearance / Constraint)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-GEO-01 IN ['CRZ-I', 'CRZ-II', 'CRZ-III', 'CRZ-IV']`
- **Source**: `SRC-112`, CRZ Notification 2019 paras 4(i), 4(ii), 4(xi)
- **Effective Date**: `2019-01-18`
- **Authority**: `MCZMA / MoEFCC`
- **Critical Finding**: Para 4(i) of the CRZ Notification 2019 enacts a statutory prohibition against setting up new industries or expanding existing industries within Coastal Regulation Zones. Encoding this as a trigger that outputs `APPLIES` treats a statutory prohibition as an approval application.
- **Verdict**: **BLOCKING**.

### Rule `R-084`: Forest Land Non-Forest Use Approval (`LOC-FOREST`)
- **Approval Target**: `LOC-FOREST` (Forest Land Diversion Clearance)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-LOC-15 == True`
- **Source**: `SRC-113`, Van (Sanrakshan Evam Samvardhan) Rules 2023 Rules 9, 10
- **Effective Date**: `2023-12-01`
- **Authority**: `MoEFCC / Regional Office / State Forest Dept`
- **Evaluation**: Grounded in Van Adhiniyam 1980 / Rules 2023. Prior Central approval is required for diversion of forest land. Target is a location trigger (`location_triggers.csv`). Register required_inputs also cited `F-GEO-03` (area in ha) which routes authority between Regional Office and Central Ministry.
- **Verdict**: **NEEDS_REVIEW** *(Subsystem categorization; authority routing area unmodeled)*.

### Rule `R-086`: Boiler Registration Trigger (`APR-023`)
- **Approval Target**: `APR-023` (Boiler Registration under Boilers Act 2025)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `R-028 tree AND F-BLR-07 == 'NOT_REGISTERED'`
- **Source**: `SRC-034`, Boilers Act 2025 Section 12(1)-(6)
- **Effective Date**: `2025-05-01`
- **Authority**: `AUT-007` (Directorate of Steam Boilers)
- **Evaluation**: Legally accurate and deterministic: if a unit has an apparatus meeting the statutory boiler definition (`R-028`) and is not currently registered (`F-BLR-07 == 'NOT_REGISTERED'`), registration under Section 12 is mandatory prior to use.
- **Verdict**: **SAFE**.

### Rule `R-087`: Existing 1923 Act Boilers Deemed Registration (`APR-023`)
- **Approval Target**: `APR-023` (Boiler Registration)
- **Role**: `RuleRole.TRIGGER` *(Defective staging)*
- **Condition**: `F-BLR-07 == 'REGISTERED_UNDER_1923_ACT'`
- **Source**: `SRC-034`, Boilers Act 2025 Section 45(2)(f)
- **Effective Date**: `2025-05-01`
- **Authority**: `AUT-007` (Directorate of Steam Boilers)
- **Critical Finding**: Section 45(2)(f) provides that any boiler registered under the repealed 1923 Act shall be deemed to be registered under the 2025 Act. Encoded with role `TRIGGER`, it evaluates to `APPLIES` under `APR-023`, incorrectly demanding fresh registration.
- **Verdict**: **BLOCKING** *(Requires migration to deemed status / exemption)*.

### Rule `R-089`: Inter-State Migrant Workmen Registration (`APR-022`)
- **Approval Target**: `APR-022` (ISMW Registration of Principal Employer)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-LAB-08 >= 10`
- **Source**: `SRC-081`, OSH Code 2020 Section 59
- **Effective Date**: `2025-11-21`
- **Authority**: `AUT-006` (Labour Commissioner)
- **Evaluation**: Direct statutory transcription of OSH Code Section 59 establishing threshold of 10 or more inter-state migrant workers.
- **Verdict**: **SAFE**.

### Rule `R-093`: CMVR Table III Dangerous Goods Consignor Duties (`CMP-024`)
- **Approval Target**: `CMP-024` (Consignor Transport Duties)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-TRN-01 == True`
- **Source**: `SRC-102`, Central Motor Vehicles Rules 1989 Rule 131
- **Effective Date**: `None` in code (`1993` in register)
- **Authority**: `""` in code (`"-"` in register)
- **Evaluation**: Rule 131 sets forth operational transport duties for consignors. It is a continuous compliance duty (`compliance.csv`), not an approval clearance. Effective date is year-only (`1993`).
- **Verdict**: **NEEDS_REVIEW**.

### Rule `R-094`: Bulk E-Waste Handover Duty (`CMP-025`)
- **Approval Target**: `CMP-025` (Bulk E-Waste Handover Obligation)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-EEE-01 >= 1000`
- **Source**: `SRC-135`, E-Waste (Management) Rules 2022 Rules 3, 8
- **Effective Date**: `2023-04-01`
- **Authority**: `""` in code (`"-"` in register)
- **Evaluation**: Threshold of 1,000 units of Schedule-I EEE defines a bulk consumer under Rule 3, triggering disposal duties under Rule 8. It is an ongoing operational duty rather than an application clearance.
- **Verdict**: **NEEDS_REVIEW**.

### Rule `R-096`: Hazardous Waste Schedule II Characteristic Test (`APR-010`)
- **Approval Target**: `APR-010` (HOWM Form 1 -> Form 2 Authorisation)
- **Role**: `RuleRole.TRIGGER`
- **Condition**: `F-HW-04 IN ['CLASS_A', 'CLASS_B', 'CLASS_C1', 'CLASS_C2', 'CLASS_C3', 'CLASS_A_TCLP', 'CLASS_C1_FLAMMABLE', 'CLASS_C2_CORROSIVE', 'CLASS_C3_REACTIVE', 'HAZARDOUS', 'MEETS_SCHEDULE_II']`
- **Source**: `SRC-120` (Tier-2), HOWM Rules 2016 Schedule II Class A/B/C
- **Effective Date**: `2016-04-04`
- **Authority**: `AUT-003` (MPCB)
- **Evaluation**: Rigorously verified in `audit_mh_hazardous_waste_authorization_chain.md`. Evaluates laboratory test findings against statutory Schedule II criteria using closed token matching. Fails closed when facts are missing.
- **Verdict**: **SAFE**.

---

## 5. Summary of Audit Findings & Remediation Roadmaps

### 5.1. Blocking Findings (Must Be Addressed Before Full Production Cutover)

1. **`R-030` Petroleum Exemption Semantic Inversion (`APR-026`)**:
   - *Problem*: `R-030` is an exemption (Section 7(i) Petroleum Act), but active as `TRIGGER`. Fulfilling exemption conditions outputs `APPLIES`.
   - *Remediation*: Migrate `R-030` to `RuleRole.EXEMPTION` in `MH_APPROVAL_COMPOSITIONS["APR-026"]` with a corresponding trigger rule or deferred trigger placeholder, preventing false `APPLIES` outcomes.

2. **`R-087` Boilers Act Deemed-Registered Inversion (`APR-023`)**:
   - *Problem*: Units registered under the 1923 Act are deemed registered under s.45(2)(f). Active `TRIGGER` role demands fresh registration.
   - *Remediation*: Migrate `R-087` to `RuleRole.EXEMPTION` / deemed status under `APR-023`.

3. **`R-077` CGWA Over-Exploited Prohibition Conflation (`APR-043`)**:
   - *Problem*: Statutory ban on granting abstraction NOCs in Over-Exploited units is encoded as a trigger producing `APPLIES`.
   - *Remediation*: Split `R-077` into an explicit statutory prohibition node in orchestration or defer from returning `APPLIES`.

4. **`R-083` CRZ Siting Prohibition (`LOC-CRZ`)**:
   - *Problem*: Siting prohibition under CRZ Notification 2019 para 4(i) is represented as an applicable approval clearance.
   - *Remediation*: Relocate to a dedicated site permissibility / constraint checker rather than an `ApprovalRule`.

5. **`R-035` MIDC Plot Allotment Guard (`APR-029`)**:
   - *Problem*: Automatically triggers Plot Allotment for any site in an MIDC estate without statutory locator or distinguishing existing plot holders.
   - *Remediation*: Defer `R-035` or guard with an `existing_plot_held` fact.

### 5.2. Non-Blocking / Needs-Review Findings

1. **Missing Precise Clause Locators**:
   - `R-046` cites `SRC-052` with locator `"-"`. Enrich citation with the specific section on construction dewatering.
2. **Year-Only Effective Dates**:
   - `R-030` (2002), `R-056` (2016), `R-067` (1968), `R-093` (1993) have year-only dates in register. Preserving `None` in code respects RULE 1 (never invent month/day precision), but should be formally documented.
3. **State Licensing Authority Disambiguation**:
   - `R-067` designates authority as `"Licensing officer (State; identity in MH UNKNOWN)"`. Official Maharashtra Agriculture Department gazette notification required to confirm specific official post.
4. **Architectural Separation of Approvals vs Ongoing Duties**:
   - `CMP-018`, `CMP-024`, and `CMP-025` belong to the compliance monitoring domain (`compliance.csv`) rather than initial project approval applicability (`approvals.csv`). While mathematically safe, they should eventually be migrated to an operational compliance engine.

---

## 6. Audit Conclusion & Certification Statement

The active Maharashtra rule set consists of **26 rules**.
- **15 rules are certified SAFE**: They represent traceable, evidence-grounded statutory provisions whose mathematical formulations and engine roles accurately reflect the law.
- **6 rules are designated NEEDS_REVIEW**: Their legal evidence is sound, but documentary refinements (locators, dates, authority naming, or subsystem boundaries) are noted.
- **5 rules are designated BLOCKING**: They exhibit semantic role inversions (exemptions acting as triggers) or statutory prohibitions presented as applicable approvals. These rules must undergo planned exception-role migration or deferral before Maharashtra is promoted to production default (`DEFAULT_JURISDICTION = "IN-MH"`).

*Per task instructions, zero production code or rule files were altered during this audit.*
