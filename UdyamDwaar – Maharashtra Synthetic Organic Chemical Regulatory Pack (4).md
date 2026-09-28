# UdyamDwaar – Maharashtra Synthetic Organic Chemical Regulatory Pack (v5 verification pass)

Project UdyamDwaar (SIH26130). This covers the archetype of a specialty/synthetic organic chemical manufacturer in Maharashtra. No site, estate, company, plot, product or inventory is hard-coded; every such fact is an engine input. The v4 pack is the baseline, and every v5 change is logged in `csv/changelog_v5.csv`. All counts in this report are computed from the CSV tables at build time.

## 1. Executive summary

**The dataset is NOT complete.** 17 unresolved items remain open or partial, All 20 quality gates PASS, but the gates test structure and traceability, not legal completeness. The engine can run the IMPLEMENTATION_SAFE subset. It fails closed: any missing input returns INSUFFICIENT_DATA, UNKNOWN never becomes DOES_NOT_APPLY, and DO_NOT_IMPLEMENT records never enter orchestration.

| metric | value |
|---|---|
| active rules | 105 |
| IMPLEMENTATION_SAFE / REQUIRES_CONFIRMATION / DO_NOT_IMPLEMENT | 76 / 26 / 3 |
| UNKNOWN rules (hard block or fail-closed guard) | 3 |
| conflicts | 28 |
| unresolved items (open/partial) | 17 |
| sources (T1 / other) | 188 (70 / 118) |
| MSIHC rows by status | VERIFIED 218, REQUIRES_OFFICIAL_CONFIRMATION 2, VERIFIED_CONDITIONAL 1 |
| v5 changes (corrections / additions / new tables / list moves) | 591 (456 / 73 / 13 / 49) |
| CSV tables | 69 |

## 2. Research cutoff

The cutoff is 26-09-2026. All sources were accessed on that date. Snippets, blogs and LinkedIn posts were used only to find leads and are never cited as evidence. Where an official page could not be reached, the item stays UNKNOWN or NOT_FOUND.

## 3. Sources used

The register has 188 sources, by tier: T1 70, T2 31, T3 67, T4 9, T5 11. The v5 additions are listed below. Three v4 sources were re-tiered to T2 as official consolidated or explanatory texts (see Changelog).

| id | tier | source | date | locator |
|---|---|---|---|---|
| SRC-166 | T1 | [MWRRA Prohibition Order dated 31-07-2015 under MH Groundwater Act 2009](https://mwrra.maharashtra.gov.in/wp-content/uploads/2022/08/Prohibition-Order.pdf) | 31-07-2015 | Order paras 1-4 (p.1-2); annexure village list |
| SRC-167 | T1 | [MSIHC Rules 1989 as amended up to date - India Code central consolidat](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_16_18_00011_198629_1517807327582&type=rule&filename=msihc_rules_ameded_upto_date.pdf) | (consolidated; last amendment 19-01-2000) | p.734 amendment list; Sch 1 p.740; Sch 2 p.746-747 footnote 4; Sch 3 p.748-752 footnotes 1 |
| SRC-168 | T2 | [MoEFCC Reply Affidavit (Director, MoEFCC) dated 16-09-2024 in NGT OA N](https://www.greentribunal.gov.in/sites/default/files/news_updates/Reply%20Affidavit%20by%20MoEF&CC%20in%20OA%20No.%20772%20of%202024%20%28NEWS%20ITEM%20TITLED%203%20SLEEPING%20AFTER%20FINISHING%20SHIFT%20KILLED%20IN%20BLAZE%20AT%20NARELA%20FACTORY%206%20INJURED.pdf) | 16-09-2024 | paras describing MSIHC Rules 1989 and amendments |
| SRC-169 | T1 | [Gas Cylinders Rules 2016 - Gazette copy G.S.R. 1081(E) 22-11-2016 (Ind](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_11_61_00011_188404_1523272950845&type=rule&filename=GCR_2016.pdf) | 22-11-2016 | r.44(a)-(c); r.48; r.51(2); r.55(2) |
| SRC-170 | T1 | [Gas Cylinders (Amendment) Rules 2025 - G.S.R. 386(E) 16-06-2025 (PESO)](https://www.peso.gov.in/web/sites/default/files/2025-11/Gas%20Cylinders%20Amendment%20Rules%202025%209-Jun-2025.pdf) | 16-06-2025 | rules 2-3 |
| SRC-171 | T1 | [Gas Cylinders (Amendment) Rules 2025 - G.S.R. 839(E) 12-11-2025 (PESO)](https://peso.gov.in/web/sites/default/files/2025-12/GCR%20Amendment%20Rules%2012-Nov-2025.pdf) | 12-11-2025 | rule 2 (r.2 clause xxviii) |
| SRC-172 | T1 | [Draft Gas Cylinders (Amendment) Rules 2026 - G.S.R. 103(E) 03-02-2026 ](https://egazette.gov.in/WriteReadData/2026/269821.pdf) | 03-02-2026 | whole |
| SRC-173 | T1 | [Gas Cylinders (Amendment) Rules 2026 - G.S.R. 315(E) 27-04-2026, Gazet](https://www.dpiit.gov.in/static/uploads/2026/06/f3aced8168f77a505b4bfcac28894329.pdf) | 28-04-2026 | rules 2-4 (r.3(5), r.32(1) proviso, r.48(3)(b)) |
| SRC-174 | T1 | [SMPV(U) Rules 2016 - bilingual Gazette text G.S.R. 1109(E) 01-12-2016 ](https://peso.gov.in/web/sites/default/files/2019-12/SMPV_RULES_2016_bilingual.pdf) | 01-12-2016 | r.2(ix), r.2(xxxvii), r.3, r.45, r.46(1)(i)(c), r.47, r.51 |
| SRC-175 | T1 | [SMPV(U) (Amendment) Rules 2025 - G.S.R. 283(E) 28-04-2025 (DPIIT)](https://www.dpiit.gov.in/static/uploads/2025/10/f4bb848d64bc783149ee2ca855ca46e3.pdf) | 28-04-2025 | Schedule I Table C |
| SRC-176 | T1 | [Draft SMPV(U) (Amendment) Rules 2026 - G.S.R. 147(E) 24-02-2026 (DRAFT](https://peso.gov.in/web/sites/default/files/2026-03/SMPV%20Amdnemnt%20draft%202026.pdf) | 24-02-2026 | whole |
| SRC-177 | T1 | [SMPV(U) (Amendment) Rules 2026 - G.S.R. 448(E) 05-06-2026, Gazette No.](https://peso.gov.in/web/sites/default/files/2026-06/SMPV%20Amendment%20Rules%202026%2005-06-2026.pdf) | 05-06-2026 | rule 1(2); rule 4 ('rule 47 shall be omitted'); r.21(17); r.22(3); r.51(4) |
| SRC-178 | T2 | [MoEF Circular J-13011/81/2006-IA II(I) 06-02-2007 - Clarification rega](https://jseiaa.in/uploads/notification/1721631251.pdf) | 06-02-2007 | whole |
| SRC-179 | T1 | [Supreme Court - Vanashakti v Union of India, WP(C) 166/2025, judgment ](https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/IA_DOCS/1002_01092025113231.pdf) | 05-08-2025 | operative directions |
| SRC-180 | T1 | [MoEFCC OM F.No. IA-J-11011/152/2025-IA-II(I) 11-12-2025 (SAF under ite](https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/IA_DOCS/1002_12122025094106.pdf) | 11-12-2025 | whole |
| SRC-181 | T1 | [Battery Waste Management (Amendment) Rules 2025 - S.O. 958(E) 24-02-20](https://eprbattery.cpcb.gov.in/upload/adminDoc/Battery_Waste_Management_%28Amendment%29_Rules,_2025.pdf) | 24-02-2025 | rules 1-2 (Schedule I para 2 clauses (ia), (ib), (v)) |
| SRC-182 | T1 | [HOWM (Amendment) Rules 2022 - G.S.R. 593(E) 21-07-2022 (Schedule IX, E](https://cpcb.nic.in/uploads/hwmd/HOWM-Sixth-Amendment-Rules-2022.pdf) | 21-07-2022 | Sch IX para 1(e) producer; para 2 application; para 3 registration; para 9 portal |
| SRC-183 | T1 | [HOWM - EPR for scrap of non-ferrous metals - G.S.R. 438(E) 01-07-2025 ](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_16_18_00011_198629_1517807327582&type=rule&filename=epr_for_scrap_of_non-ferrous_metals.pdf) | 01-07-2025 | commencement; r.2(k),(o),(q); r.45; r.52; r.55 |
| SRC-184 | T3 | [CPCB - Used Oil EPR portal home page](https://eprusedoil.cpcb.gov.in/) |  | home page text |
| SRC-185 | T3 | [Maharashtra Labour Department - Notifications page (state draft rules ](https://labour.maharashtra.gov.in/en/notifications) |  | rows 3-4 |
| SRC-186 | T3 | [Maharashtra Labour Department - Directorate of Steam Boilers allied-of](https://labour.maharashtra.gov.in/en/allied-offices/directorate-of-steam-boilers) |  | Acts list |
| SRC-187 | T3 | [Directorate of Steam Boilers - Online services page (RTS time limits)](https://www.mahaboiler.in/boiler/online_services.html) |  | rows 1-22 |
| SRC-188 | T3 | [PESO - Circulars page (circular 11-09-2025 'Procedural changes in resp](https://www.peso.gov.in/web/en/circular) | 11-09-2025 | circular list entry 11-09-2025 |

## 4. New evidence discovered

- **MPCB timelines.** The [MPCB circular BO/AST/EoDB/B-68 of 23-02-2026](https://www.mpcb.gov.in/sites/default/files/standing_orders/Revised-Timeline-for-Grant-Refusal-of-Consent-under-Easy-of-Doing-Business-Reforms.pdf) was read visually from its 2-page scan. The revised limits are in WORKING days: Green 15, Orange 24, Red 40. Each value sits against the CTE/CTO/Renewal columns of its category row. The circular supersedes the 28-04-2025 circular except its penal-fee provisions and takes immediate effect. It recites the central limits under 84(E) of 29-01-2025: Green 30/30/30, Orange 45/60/60, Red 60/90/120 days. It says nothing on the clock-start event, expansion or amendment consents, Blue/White categories, or GSR 62/63(E).

- **MSIHC.** The [central India Code consolidated MSIHC text](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_16_18_00011_198629_1517807327582&type=rule&filename=msihc_rules_ameded_upto_date.pdf) attributes Schedule 2 entries 12–27 to Rule 11, and the bracketed Schedule 3 column-4 values to Rule 14(a–h), of the 1994 amendment (S.O.2882, 03-10-1994). The [MoEFCC reply affidavit of 16-09-2024 (NGT OA 772/2024)](https://www.greentribunal.gov.in/sites/default/files/news_updates/Reply%20Affidavit%20by%20MoEF&CC%20in%20OA%20No.%20772%20of%202024%20%28NEWS%20ITEM%20TITLED%203%20SLEEPING%20AFTER%20FINISHING%20SHIFT%20KILLED%20IN%20BLAZE%20AT%20NARELA%20FACTORY%206%20INJURED.pdf) confirms the amendment chain 1989 → 1990 (×2) → 1994 → 2000.

- **PESO.** Primary texts were read for [Gas Cylinders Rules 2016 (Gazette)](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_11_61_00011_188404_1523272950845&type=rule&filename=GCR_2016.pdf), [SMPV(U) Rules 2016 (Gazette)](https://peso.gov.in/web/sites/default/files/2019-12/SMPV_RULES_2016_bilingual.pdf) and the [Petroleum Rules 2002](https://peso.gov.in/web/sites/default/files/2019-12/PR-2002-English-full.pdf). The [SMPV(U) Amendment Rules 2026, G.S.R. 448(E) of 05-06-2026](https://peso.gov.in/web/sites/default/files/2026-06/SMPV%20Amendment%20Rules%202026%2005-06-2026.pdf) omits rule 47 (District Authority NOC). The [GCR Amendment Rules 2026, G.S.R. 315(E)](https://www.dpiit.gov.in/static/uploads/2026/06/f3aced8168f77a505b4bfcac28894329.pdf) amends r.3(5), r.32(1) and r.48(3)(b).

- **Groundwater.** The [MWRRA Prohibition Order of 31-07-2015](https://mwrra.maharashtra.gov.in/wp-content/uploads/2022/08/Prohibition-Order.pdf) prohibits new deep wells over 60 m for agriculture or industry in 80 notified watersheds across 13 districts. Drinking-water permission is granted by the Sub-Divisional Officer on GSDA advice.

- **EPR.** The following gazettes were read: [tyre Schedule IX (G.S.R. 593(E) 2022)](https://cpcb.nic.in/uploads/hwmd/HOWM-Sixth-Amendment-Rules-2022.pdf), [non-ferrous scrap EPR (G.S.R. 438(E), in force 01-04-2026)](https://upload.indiacode.nic.in/showfile?actid=AC_CEN_16_18_00011_198629_1517807327582&type=rule&filename=epr_for_scrap_of_non-ferrous_metals.pdf) and [BWM Amendment 2025 (S.O. 958(E))](https://eprbattery.cpcb.gov.in/upload/adminDoc/Battery_Waste_Management_%28Amendment%29_Rules,_2025.pdf). The used-oil instrument was identified only from the [CPCB portal](https://eprusedoil.cpcb.gov.in/).

- **MFS Annexure A.** The pages of the [MFS office order of 10-09-2014](https://mahafireservice.gov.in/circular/Office%20Order-MFS-Fire%20Prevention%20in%20Industrial%20Occupancies%20with%20Annx-A%20%26%20A-1-dtd.10.09.2014.pdf) are clean vector renders, so all 15 bands × 13 columns were read.

- **Labour, boilers, EIA.** The [Labour Dept notifications page](https://labour.maharashtra.gov.in/en/notifications) still lists only draft MH OSH rules. The boiler portal pages are inconsistent: [DSB acts page](https://mahaboiler.in/boiler/acts.html) vs [Labour Dept DSB page](https://labour.maharashtra.gov.in/en/allied-offices/directorate-of-steam-boilers). For EIA, the [Supreme Court judgment of 05-08-2025](https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/IA_DOCS/1002_01092025113231.pdf), the [MoEF circular of 06-02-2007](https://jseiaa.in/uploads/notification/1721631251.pdf) and the [OM of 11-12-2025](https://parivesh.nic.in/publicdocument/UPLOAD_OM_NOTIFICATION/IA_DOCS/1002_12122025094106.pdf) were checked, and none resolves the 5(f)+8(a) question.

## 5. Corrections to v4

| change | table | record | field | v4 value | v5 value |
|---|---|---|---|---|---|
| V5-0027 | sla | SLA-001 | clock_start | Complete application (per circular) | UNKNOWN (circular does not state the clock-start event) |
| V5-0034 | sla | SLA-001 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_CONDITIONAL |
| V5-0035 | sla | SLA-002 | clock_start | Complete application | UNKNOWN (circular does not state the clock-start event) |
| V5-0042 | sla | SLA-002 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_CONDITIONAL |
| V5-0043 | sla | SLA-003 | clock_start | Complete application | UNKNOWN (circular does not state the clock-start event) |
| V5-0050 | sla | SLA-003 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_CONDITIONAL |
| V5-0105 | msihc_t1_thresholds | S2-12 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0106 | msihc_t1_thresholds | S2-12 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0107 | msihc_t1_thresholds | S2-12 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0108 | msihc_t1_thresholds | S2-12 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0111 | msihc_t1_thresholds | S2-13 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0112 | msihc_t1_thresholds | S2-13 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0113 | msihc_t1_thresholds | S2-13 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0114 | msihc_t1_thresholds | S2-13 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0117 | msihc_t1_thresholds | S2-14 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0118 | msihc_t1_thresholds | S2-14 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0119 | msihc_t1_thresholds | S2-14 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0120 | msihc_t1_thresholds | S2-14 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0123 | msihc_t1_thresholds | S2-15 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0124 | msihc_t1_thresholds | S2-15 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0125 | msihc_t1_thresholds | S2-15 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0126 | msihc_t1_thresholds | S2-15 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0129 | msihc_t1_thresholds | S2-16 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0130 | msihc_t1_thresholds | S2-16 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0131 | msihc_t1_thresholds | S2-16 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0132 | msihc_t1_thresholds | S2-16 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0135 | msihc_t1_thresholds | S2-17 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0136 | msihc_t1_thresholds | S2-17 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0137 | msihc_t1_thresholds | S2-17 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0138 | msihc_t1_thresholds | S2-17 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0141 | msihc_t1_thresholds | S2-19 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0142 | msihc_t1_thresholds | S2-19 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0143 | msihc_t1_thresholds | S2-19 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0144 | msihc_t1_thresholds | S2-19 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0147 | msihc_t1_thresholds | S2-20 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0148 | msihc_t1_thresholds | S2-20 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0149 | msihc_t1_thresholds | S2-20 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0150 | msihc_t1_thresholds | S2-20 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0153 | msihc_t1_thresholds | S2-21 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0154 | msihc_t1_thresholds | S2-21 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0155 | msihc_t1_thresholds | S2-21 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0156 | msihc_t1_thresholds | S2-21 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0159 | msihc_t1_thresholds | S2-22 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0160 | msihc_t1_thresholds | S2-22 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0161 | msihc_t1_thresholds | S2-22 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0162 | msihc_t1_thresholds | S2-22 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0165 | msihc_t1_thresholds | S2-23 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0166 | msihc_t1_thresholds | S2-23 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0167 | msihc_t1_thresholds | S2-23 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0168 | msihc_t1_thresholds | S2-23 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0171 | msihc_t1_thresholds | S2-24 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0172 | msihc_t1_thresholds | S2-24 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0173 | msihc_t1_thresholds | S2-24 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0174 | msihc_t1_thresholds | S2-24 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0177 | msihc_t1_thresholds | S2-25 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0178 | msihc_t1_thresholds | S2-25 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0179 | msihc_t1_thresholds | S2-25 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0180 | msihc_t1_thresholds | S2-25 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0183 | msihc_t1_thresholds | S2-26 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0184 | msihc_t1_thresholds | S2-26 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0185 | msihc_t1_thresholds | S2-26 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0186 | msihc_t1_thresholds | S2-26 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0189 | msihc_t1_thresholds | S2-27 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0190 | msihc_t1_thresholds | S2-27 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0191 | msihc_t1_thresholds | S2-27 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0192 | msihc_t1_thresholds | S2-27 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0195 | msihc_t1_thresholds | S2-18 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_T1_CONSOLIDATED |
| V5-0196 | msihc_t1_thresholds | S2-18 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION | REQUIRES_OFFICIAL_CONFIRMATION (printed '501' in SRC-167 and SRC-155;  |
| V5-0197 | msihc_t1_thresholds | S2-18 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_CONDITIONAL |
| V5-0198 | msihc_t1_thresholds | S2-18 | source_id | SRC-155;SRC-158 | SRC-167;SRC-155 |
| V5-0201 | msihc_t1_thresholds | S3P1-101 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0202 | msihc_t1_thresholds | S3P1-101 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0203 | msihc_t1_thresholds | S3P1-101 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0206 | msihc_t1_thresholds | S3P1-106 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0207 | msihc_t1_thresholds | S3P1-106 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0208 | msihc_t1_thresholds | S3P1-106 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0211 | msihc_t1_thresholds | S3P1-109 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0212 | msihc_t1_thresholds | S3P1-109 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0213 | msihc_t1_thresholds | S3P1-109 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0216 | msihc_t1_thresholds | S3P1-110 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0217 | msihc_t1_thresholds | S3P1-110 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0218 | msihc_t1_thresholds | S3P1-110 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0221 | msihc_t1_thresholds | S3P1-112 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0222 | msihc_t1_thresholds | S3P1-112 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0223 | msihc_t1_thresholds | S3P1-112 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0226 | msihc_t1_thresholds | S3P1-117 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0227 | msihc_t1_thresholds | S3P1-117 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0228 | msihc_t1_thresholds | S3P1-117 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0231 | msihc_t1_thresholds | S3P1-122 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0232 | msihc_t1_thresholds | S3P1-122 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0233 | msihc_t1_thresholds | S3P1-122 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0236 | msihc_t1_thresholds | S3P1-123 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0237 | msihc_t1_thresholds | S3P1-123 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0238 | msihc_t1_thresholds | S3P1-123 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0241 | msihc_t1_thresholds | S3P1-144 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0242 | msihc_t1_thresholds | S3P1-144 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0243 | msihc_t1_thresholds | S3P1-144 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0246 | msihc_t1_thresholds | S3P1-148 | col4_status | REQUIRES_OFFICIAL_CONFIRMATION (1994 gazette not obtained) | VERIFIED_T1_CONSOLIDATED |
| V5-0247 | msihc_t1_thresholds | S3P1-148 | final_status | VERIFIED_CONDITIONAL | VERIFIED |
| V5-0248 | msihc_t1_thresholds | S3P1-148 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0251 | msihc_t1_thresholds | S3P1-099 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_PRIMARY_GAZETTE |
| V5-0252 | msihc_t1_thresholds | S3P1-099 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0253 | msihc_t1_thresholds | S3P1-099 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0257 | msihc_t1_thresholds | S3P1-049 | col3_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_PRIMARY_GAZETTE |
| V5-0258 | msihc_t1_thresholds | S3P1-049 | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED |
| V5-0259 | msihc_t1_thresholds | S3P1-049 | source_id | SRC-154;SRC-155 | SRC-154;SRC-167;SRC-155 |
| V5-0280 | rules | R-033 | source_id | SRC-093;SRC-019;SRC-018 | SRC-169;SRC-173 |
| V5-0282 | rules | R-033 | condition | GCR_EXEMPT := own use AND not for sale AND for every gas gro | GCR_EXEMPT := own use AND not for sale/trading AND per gas group at a  |
| V5-0285 | rules | R-033 | final_status | DO_NOT_IMPLEMENT_YET | VERIFIED_CONDITIONAL |
| V5-0286 | rules | R-034 | source_id | SRC-094;SRC-020 | SRC-174;SRC-177 |
| V5-0290 | peso_gating | Gas Cylinders Rules 2016 r.44 exemptions | gate | DO_NOT_IMPLEMENT_YET | VERIFIED_CONDITIONAL |
| V5-0329 | epr_regimes | EPR-TYRE | final_status | REQUIRES_OFFICIAL_CONFIRMATION | VERIFIED_CONDITIONAL |
| V5-0344 | rules | R-097 | source_id | SRC-132;SRC-131 | SRC-166;SRC-131;SRC-132 |
| V5-0346 | rules | R-097 | condition | MH_GW_DEEP_WELL := F-GW-02 >= 60 m AND purpose IN {agricultu | MH_GW_DEEP_WELL_PROHIBITION := IF F-GW-02 > 60 m AND purpose IN {agric |
| V5-0355 | rules | R-007 | source_id | SRC-001 | SRC-001;SRC-179 |
| V5-0362 | rules | R-036 | final_status | VERIFIED_CONDITIONAL | REQUIRES_OFFICIAL_CONFIRMATION |
| V5-0364 | rules | R-037 | final_status | VERIFIED_CONDITIONAL | REQUIRES_OFFICIAL_CONFIRMATION |
| V5-0367 | sources | SRC-095 | tier | T3 (official compilation) | T2 |
| V5-0369 | sources | SRC-098 | tier | T3 | T2 |
| V5-0371 | sources | SRC-099 | tier | T3 | T2 |
| V5-0372 | rules | R-074 | final_status | VERIFIED_CONDITIONAL | UNKNOWN |

## 6. Verified rules

| rule | title | status | source | locator | effective |
|---|---|---|---|---|---|
| R-059 | INCENTIVE_VALUE  | VERIFIED | SRC-073;SRC-074 | - | - |
| R-071 | MH_GW_ACT_IN_FORCE  | VERIFIED | SRC-131;SRC-132 | s.1(3); s.8 | 2014-06-01 |
| R-075 | Prior Environmental Clearance - Schedule item 5(f) Synt | VERIFIED | SRC-001 | para 9 | 2026-07-13 |
| R-076 | EC_COMPLIANCE_DUE  | VERIFIED | SRC-001 | para 10(ii) | 2026-07-13 |
| R-086 | Boiler registration | VERIFIED | SRC-034 | s.12(1)-(6) | 2025-05-01 |
| R-087 | Boiler registration | VERIFIED | SRC-034 | s.45(2) | 2025-05-01 |
| R-088 | BOILER_CERT_CEASES  | VERIFIED | SRC-034 | s.13(1)(a)-(f); s.15 | 2025-05-01 |
| R-103 | SMPV(U) licence (LS-1A) and prior approval | VERIFIED | SRC-174;SRC-177 | r.47(1); G.S.R. 448(E) rule 4 | 2016-12-01 |

## 7. Conditional rules

There are 68 VERIFIED_CONDITIONAL rules. They are implementation-safe, but applicability depends on input facts, and some have noted currency gaps. The full list is in `rule_register_v5.csv`. Those new or changed in v5:

| rule | title | status | source | locator | effective |
|---|---|---|---|---|---|
| R-007 | Prior EC - item 8(a) Building & construction | VERIFIED_CONDITIONAL | SRC-001;SRC-179 | Item 8(a) | 2006-09-14 |
| R-033 | Gas cylinder storage licence (Form F) | VERIFIED_CONDITIONAL | SRC-169;SRC-173 | GCR 2016 r.44(a),(b)(i)-(iv) (Gazette G.S.R.1081(E)); r.44(c | 2016 |
| R-100 | Petroleum storage licence (Form XII/XIII District Autho | VERIFIED_CONDITIONAL | SRC-117 | r.142(2); r.148(1)-(2) | 2002-03-18 |
| R-101 | Gas cylinder storage licence (Form F) | VERIFIED_CONDITIONAL | SRC-169 | r.51(2); r.55(2) | 2016-11-22 |
| R-102 | SMPV(U) licence (LS-1A) and prior approval | VERIFIED_CONDITIONAL | SRC-174 | r.51(1); r.55(2) | 2016-12-01 |
| R-104 | Gas cylinder storage licence (Form F) | VERIFIED_CONDITIONAL | SRC-169;SRC-173 | r.48(1),(2),(3); G.S.R. 315(E) r.48(3)(b) | 2016-11-22 |
| R-105 | PLANNING_ZONE_PERMISSIBILITY  | VERIFIED_CONDITIONAL | SRC-123;SRC-124 | MRTP s.2(19), s.44; UDCPR Reg.1.4(iii) | - |

## 8. Unknown rules

| rule | condition | status |
|---|---|---|
| R-015 | UNIT_CATEGORY (multiple sector codes) := UNKNOWN | VERIFIED_CONDITIONAL |
| R-052 | CETP := F-WAT-03 == 'CETP' AND F-WAT-04 == TRUE | UNKNOWN |
| R-074 | EC_5F_AND_8A := UNKNOWN when EC_5F_REQUIRED==TRUE AND EC_8A==TRUE (text silent on combination) | UNKNOWN |

R-074 (EIA 5(f)+8(a)) is the only hard block. The others are fail-closed guards that return UNKNOWN or INSUFFICIENT_DATA by design.

## 9. Requires-confirmation rules

| rule | title | source | reason |
|---|---|---|---|
| R-005 | Prior Environmental Clearance - Schedule item 5(f) Synt | SRC-001 | Scope of coverage (which units) must be read from the estate EC; do not auto-exempt |
| R-006 | Prior EC - item 5(e) Petrochemical based processing | SRC-001 |  |
| R-010 | EC for industrial estate - item 7(c) (estate developer, | SRC-001 | Informational |
| R-022 | Factory plan approval | SRC-081;SRC-030 | s.2(1)(w) proviso: where a State law in force immediately before the Code specified a diff |
| R-023 | Factory registration & licence (MAH/Hazardous vs other) | SRC-029 | 'Hazardous process' criterion not encoded - UNKNOWN |
| R-025 | Shops & Establishments intimation (<10 workers) | SRC-027 |  |
| R-034 | SMPV(U) licence (LS-1A) and prior approval | SRC-174;SRC-177 | v5: official Gazette text read (definitions). 2018/2019/2021/2025 (374(E), 422(E)) amendme |
| R-036 | MIDC combined building permission + provisional fire NO | SRC-043;SRC-044 | Portal evidence only (PORTAL_SERVICE_EXISTS). Legal basis cited as 'MIDC DCR' but the regu |
| R-037 | MIDC occupancy certificate | SRC-044 | Portal evidence only (PORTAL_SERVICE_EXISTS). Legal basis cited as 'MIDC DCR' but the regu |
| R-038 | MIDC water connection | SRC-043 |  |
| R-039 | MIDC tree felling permission | SRC-043;SRC-070 |  |
| R-040 | MIDC change in manufacturing activity | SRC-043 |  |
| R-042 | Provisional fire NOC (non-MIDC) | SRC-048 | Applicability: Schedule-I lists Industrial (G-1/G-2/G-3), Storage (H) and Hazardous (J) bu |
| R-048 | Electrical installation approval / energisation | SRC-042;SRC-041 | Central Government notified 11 kV as self-certification voltage for its jurisdiction; each |
| R-049 | Lift erection permission and lift licence | SRC-041 | Goods-lift/hoist coverage not verified |
| R-051 | AAI height clearance NOC | SRC-063 |  |
| R-052 | CETP membership / discharge arrangement | - | F-WAT-04 UNKNOWN -> UNKNOWN; never assume |
| R-053 | Permission to draw water from river/public tanks | SRC-070 |  |
| R-057 | MSME_CLASS  | SRC-061 | If either input UNKNOWN -> UNKNOWN (do not classify on investment alone) |
| R-063 | Consent to Operate (Water & Air Acts) | SRC-006 | Column-to-category mapping (presumably Red/Orange/Green) UNK-031 |
| R-068 | Drug (bulk drug/API) manufacturing licence | SRC-101 |  |
| R-069 | Explosives licence (manufacture/possession) | SRC-107 |  |
| R-074 | Prior Environmental Clearance - Schedule item 5(f) Synt | SRC-001 | UNK-010. v5 official-source check: SC Vanashakti 05-08-2025 (Note 1 of 8(a) quashed - R-00 |
| R-090 | BOCW establishment registration (construction phase) | SRC-081 |  |
| R-097 | MH_GW_DEEP_WELL_PROHIBITION  | SRC-166;SRC-131;SRC-132 | v5: primary order located (T1). Order is 'until further orders'; no revocation/modificatio |
| R-098 | MATHADI  | SRC-128 |  |

Non-rule records that also need confirmation: 26 (MSIHC cells, EPR regimes, FR-03, approvals and compliance items). See `requires_confirmation.csv`.

## 10. Do-not-implement rules

| rule | title | status | reason |
|---|---|---|---|
| R-016 | Consent to Establish (Water & Air Acts) | DO_NOT_IMPLEMENT_YET | DO_NOT_IMPLEMENT_YET - MH operative detail and Red-category applicability UNKNOWN |
| R-029 | Petroleum storage licence (Form XII/XIII District Autho | DO_NOT_IMPLEMENT_YET | Class A small-quantity exemption (<=30 L) sourced only from PESO SOP (T3); Petroleum Rules |
| R-058 | INCENTIVE_BASKET  | DO_NOT_IMPLEMENT_YET | PSI under IISP 2025 not found after exhaustive search (incentive_search_log.csv). PSI 2019 |

The do-not-implement list has 24 rows in total, including incentive amounts, the one-time CTO fee, the draft groundwater Rules 2018 and superseded tables.

## 11. Regulatory conflicts

| id | topic | A | B | legal status | resolution | status |
|---|---|---|---|---|---|---|
| CON-001 | MIDC occupancy certificate time limit | SRC-043 services portal (AllServicesPortalAnon): 10 days | SRC-110 AllServicesAnon / SRC-044 planning page; SRC-046 EoD | RTS-notified legal limit not read (UNK-037) | RESOLVED - RTS notification 06-05-2025 gives the legal time  | VERIFIED |
| CON-001B | MIDC combined BP + provisional fire NOC | SRC-043: 35 days | SRC-044 / SRC-045: 15 days (BP+fire) / prov fire 30 days | RTS legal limit UNKNOWN | RESOLVED - RTS notification 06-05-2025 gives the legal time  | VERIFIED |
| CON-001C | MIDC tree felling and commencement intimation | SRC-043: tree 45 d; commencement 0 d | SRC-045/SRC-047: tree 60 d; commencement 30 d | UNKNOWN | RESOLVED - RTS notification 06-05-2025 gives the legal time  | VERIFIED |
| CON-002 | MAITRI service/department counts | SRC-057/059/070: 119 services / 15 departments | SRC-058: 128 services / 14 departments | Not legal | Counts not used in logic | VERIFIED_CONDITIONAL |
| CON-003 | Consent processing timelines | SRC-008 MPCB 23-02-2026: Green 15 / Orange 24 / Red 40 WORKI | SRC-006 central guidelines: Central outer limits (84(E)/85(E | Both operative; MPCB target is shorter and do | Display both separately; never merge. Legal consequences of  | VERIFIED_CONDITIONAL |
| CON-004 | Boilers law cited by Maharashtra | SRC-032/SRC-034 (Boilers Act 2025 in force 01-05-2025): 2025 | SRC-036 Directorate page (01-09-2026) cites 1923 Act; SRC-08 | Central Act governs (T1) | Treat services as PORTAL LEGACY SERVICE under 2025 Act; do n | VERIFIED_CONDITIONAL |
| CON-005 | Labour-code dates on Maharashtra page | SRC-025: launched 21.12.2025; rules 'framed and notified' ye | SRC-080 S.O.5321(E): commencement 21-11-2025 | Gazette governs | Use Gazette | VERIFIED_CONDITIONAL |
| CON-006 | CTO validity | SRC-006 GSR 62/63 (T1): CTO valid till cancelled; one-time f | SRC-069 MPCB auto-renewal (T2): fixed validity 5/10/15 yrs;  | Central guidelines later in time and T1; MPCB | Do not compute validity; display both with status | REQUIRES_OFFICIAL_CONFIRMATION |
| CON-007 | Lifts regime | SRC-083 (2017 Act) / SRC-084 (2026 Bill): new Act enacted; n | SRC-041 CEI RTS: services under Bombay Lifts Act 1939 | No commencement notification found | Keep 1939 services; 2017/2026 = FUTURE_REGIME | VERIFIED_CONDITIONAL |
| CON-008 | Boiler registration and renewal time limits | SRC-087 mahaboiler: registration 43 (made in MH) / 50 (outsi | SRC-088 Labour RTS page: registration 50; renewal 7 | Both official (T3); RTS notification not read | Preserve both | REQUIRES_OFFICIAL_CONFIRMATION |
| CON-009 | EIA 8(a) industrial-shed exclusion | v1 pack (APR-003/R-007) derived from S.O.523(E) Note 1: indu | SRC-001 fn 98; SRC-090/091 SC judgment: Note 1 quashed | Quashed by Supreme Court | v1 corrected; F-BLD-02 deprecated | VERIFIED_CONDITIONAL |
| CON-010 | Factory headcount threshold | SRC-081 OSH s.2(1)(w): 20 with power / 40 without; State pre | SRC-030 DISH FAQ: 20 / 40 | Code in force | Use 20/40 with UNK-029 flag | VERIFIED_CONDITIONAL |
| CON-011 | Petroleum Class B exemption wording | SRC-017 PESO SOP / SRC-106 FAQ: 'Class B (Non Bulk) <=2500 L | SRC-092 Petroleum Act s.7(i): total <=2500 L at one place an | Act (T1) governs | Implement Act test | VERIFIED_CONDITIONAL |
| CON-012 | Consent deemed CTE source | SRC-005 PIB (T3): summary | SRC-006 Gazette (T1): para 6(7) text | T1 governs | Use T1 | VERIFIED_CONDITIONAL |
| CON-013 | Renewal of fire safety approval | SRC-144 Circular 30-10-2014 (read): 'Not Necessity of renewa | SRC-145 Circular 31-01-2025 (read): 'Necessity about Renewal | MFPLSM s.3(1) refers to Renewal Fire Safety A | RESOLVED - not a conflict | VERIFIED |
| CON-014 | Petroleum Class A small-quantity storage exem | SRC-017 PESO SOP (T3): Class A <=30 L exempt | SRC-117 Petroleum Rules 2002 (T1): No such storage exemption | T1 governs | Do not implement exemption | DO_NOT_IMPLEMENT_YET |
| CON-015 | MH Groundwater Act commencement | v2 record R-071: commencement not found (UNKNOWN) | SRC-131 India Code footnote: 01-06-2014 (G.N. 28-05-2014) | T1 footnote | Adopt T1 | VERIFIED |
| CON-016 | Labour/boiler portal services cite repealed A | SRC-136 / SRC-088 Labour Dept services: Factories Act 1948,  | SRC-080 / SRC-081 / SRC-034: OSH Code in force 21-11-2025 (s | Code/Act govern; old rules saved transitional | Label services PORTAL_LEGACY; SLAs portal-only | VERIFIED_CONDITIONAL |
| CON-018 | PSI 2019 operative period | SRC-125 PSI 2019 GR: till 31-03-2024 or till new PSI comes i | SRC-126 corrigendum / SRC-061 IISP 2025: 2025 corrigendum am | Unclear | Unresolved | REQUIRES_OFFICIAL_CONFIRMATION |
| CON-019 | Groundwater regulator for industrial abstract | SRC-052 CGWA guidelines Annexure VIII: Maharashtra listed as | SRC-131/SRC-132 MH GW Act: Act in force from 01-06-2014; MWR | Both apply in their scope; CGWA inconsistency | Industrial NOC -> CGWA; MH Act deep-well/notified-area restr | VERIFIED_CONDITIONAL |
| CON-020 | Boiler registration timeline | SRC-034 Act s.12: exam date <=30 d; notice >=10 d; report <= | SRC-136 portal: 30 days (registration) | Act governs steps | Keep both, label types | VERIFIED_CONDITIONAL |
| CON-021 | MSIHC Schedule 3 Part I per-chemical threshol | v2 notes (SRC-016 India Code extraction): hydrogen 2 t; ammo | SRC-134 HSPCB scan (two extractions): hydrogen 50/200 t; amm | Gazette text governs | RESOLVED - v3 'HSPCB scan' values were extraction errors; or | VERIFIED |
| CON-024 | Annual fire renewal for Petroleum/Gas Cylinde | SRC-148 MFS Office Order 10-12-2025 para 3(III): 'certain st | SRC-117 Petroleum Rules 2002 (T1, v3): Petroleum Rules 2002  | Unverified | Keep FR-03 UNKNOWN; do not implement annual renewal | REQUIRES_OFFICIAL_CONFIRMATION |
| CON-022 | MSIHC Sch 3 Part I s.no.164 (lead styphnate)  | SRC-155 consolidated text: 50 t / 10 t (not updated) | SRC-156 S.O. 57(E) r.11(i) (+SRC-157): 100 kg for s.no.150,1 | Gazette governs | RESOLVED - use 100 kg | VERIFIED |
| CON-023 | MSIHC Sch 3 Part I s.no.111 Ethyleneimine col | SRC-154 original gazette: 50 t | SRC-155 consolidated: 5 t (no amendment footnote) | Unresolved | Hold; engine returns UNKNOWN for this entry. v5: SRC-167 rep | REQUIRES_OFFICIAL_CONFIRMATION |
| CON-026 | MSIHC Sch 3 Part I s.no.49 chemical name | SRC-154 original gazette: 4-Fluorocrotonic acid, 1 kg, CAS 3 | SRC-167 central consolidated: 4-Fluorobutyric acid, 1 kg, CA | No amending instrument renames the entry (SRC | Use gazette name + CAS for matching; threshold 1 kg VERIFIED | VERIFIED_CONDITIONAL |
| CON-027 | MSIHC Sch 3 Part I s.no.99 Warfarin | SRC-154 original gazette: 100 kg | SRC-167 central consolidated: 100 kg | Resolved | VERIFIED 100 kg | VERIFIED |
| CON-028 | Legal basis shown for boiler services | SRC-141 DSB acts page: Lists Boilers Act 2025 + 2025 rules | SRC-186 Labour Dept DSB page: Lists Boilers Act 1923 | Boilers Act 2025 operative (SRC-034, T1); por | Statute = Boilers Act 2025; display portal workflow as PORTA | VERIFIED_CONDITIONAL |

## 12. Effective-date issues

Rules by effective-date status: EXACT_DATE 61, YEAR_ONLY 25, UNKNOWN 19. A temporal query ("what applies on date X") returns INSUFFICIENT_DATA whenever the effective date is YEAR_ONLY and X falls in that year, or the date is UNKNOWN.

- MSIHC: 1994 values apply from 03-10-1994, the notification date (the commencement clause was not read), and 2000 values from 20-01-2000. No later amendment has been identified (MSIHC-AM-5, VERIFIED_CONDITIONAL). See `msihc_value_chronology.csv`.

- SMPV r.47 District Authority NOC: applies up to 04-06-2026 and is omitted from 05-06-2026 (R-103). Applications pending on 05-06-2026 → INSUFFICIENT_DATA.
- Non-ferrous EPR: in force from 01-04-2026, so earlier dates return DOES_NOT_APPLY.
- MPCB revised timelines: effective 23-02-2026. The central limits' currency after GSR 62/63(E) is unverified.
- MWRRA order: effective 31-07-2015 "until further orders". Current status is unconfirmed.

## 13. Authority uncertainties

| authority | name | authority_status |
|---|---|---|
| AUT-011 | Planning Authority (Municipal Corporation / Municipal Council / Nagar  | REQUIRES_CONFIRMATION (site/authority dependent; never defaulted) |
| AUT-012 | Maharashtra Fire & Emergency Services / local fire authority | REQUIRES_CONFIRMATION (site/authority dependent; never defaulted) |
| AUT-014 | Groundwater Surveys and Development Agency (GSDA) / Maharashtra Ground | REQUIRES_CONFIRMATION (site/authority dependent; never defaulted) |
| AUT-015 | Distribution licensee (MSEDCL / Tata Power / AEML / BEST / franchisee  | REQUIRES_CONFIRMATION (site/authority dependent; never defaulted) |
| AUT-019 | Controller of Legal Metrology, Maharashtra | REQUIRES_CONFIRMATION (site/authority dependent; never defaulted) |
| AUT-021 | Water Resources Department, GoM | REQUIRES_CONFIRMATION (site/authority dependent; never defaulted) |
| AUT-022 | Tree Authority / Tree Officer (urban local body) | REQUIRES_CONFIRMATION (site/authority dependent; never defaulted) |

No authority is ever defaulted. In particular, no distribution licensee (such as MSEDCL) and no planning authority is assumed.

## 14. Portal/integration uncertainties

| claim | evidence | INTEGRATION_STATUS |
|---|---|---|
| Service listed on MAITRI | UNKNOWN per approval (maitri_service_matrix) | UNKNOWN |
| Application submission through MAITRI | UNKNOWN - no service specification read | UNKNOWN |
| Document upload via MAITRI | UNKNOWN | UNKNOWN |
| Status tracking / real-time tracking | MAITRI site text claims 'real-time application tracking' generally (T3 statement); no per- | UNKNOWN |
| API / data exchange with UdyamDwaar | No public API specification located | UNKNOWN |
| Deep link to public MAITRI page | A hyperlink is not an integration claim | VERIFIED_CONDITIONAL |

Boilers: the statute is the Boilers Act 2025. The portal is PORTAL_LEGACY / WORKFLOW_CONFIRMATION_REQUIRED (CON-028), and this does not mean the portal is legally invalid. MIDC portal pages establish only PORTAL_SERVICE_EXISTS, so R-036/R-037 were moved to REQUIRES_CONFIRMATION.

## 15. Final unresolved register

| id | status | missing evidence | next evidence | engine behaviour |
|---|---|---|---|---|
| UR-01 | PARTIAL | Sch 2 s.no.18 (ethylene oxide) col 4 printed '501' in both official te | Gazette copy of S.O.2882 (03-10-1994) | R-020 via S2-18 -> UNKNOWN |
| UR-02 | PARTIAL | s.no.111 Ethyleneimine 50 t (gazette) vs 5 t (consolidated); s.no.49 n | MoEFCC clarification or amending instrument | s.no.111 -> UNKNOWN; s.no.49 matched by CAS |
| UR-03 | PARTIAL | Amendments 16-09-2024 to 26-09-2026; content of 1990 amendments | MoEFCC notification list | Values applied with effective dates; MSIHC-AM-5 VERIFIED_CONDITIONAL |
| UR-04 | PARTIAL | Rule requiring MFS fire renewal for PESO licensees (none found in PR/G | Unread amendments; MFS citation of a rule | F-FIR-20 UNKNOWN -> R-099 UNKNOWN; PESO licence renewal separately R-1 |
| UR-05 | OPEN (carried from v4) | Transitional rule and State fee determination | State Govt notification under GSR 62/63 para 5; MPCB order o | UNKNOWN for legacy CTOs; fee BLOCKED |
| UR-06 | OPEN | Authoritative statement on 5(f)+8(a) | MoEFCC OM/notification/court order | R-074 UNKNOWN |
| UR-07 | OPEN (carried from v4) | Scheme GR, guidelines, claim process | Industries Dept GR (not located) | All incentive computations DO_NOT_IMPLEMENT_YET; classification only |
| UR-08 | PARTIAL | Used-oil EPR gazette G.S.R.677(E) wording; non-ferrous Sch XI targets; | Gazette texts | Role-based CONDITIONAL; role UNKNOWN -> INSUFFICIENT_DATA |
| UR-09 | OPEN | LMS workflow under Boilers Act 2025 | DSB notification/forms under 2025 Act | PORTAL_LEGACY; WORKFLOW_CONFIRMATION_REQUIRED (CON-028) |
| UR-10 | PARTIAL | Unread GCR amendments (2018/2019/2022/225(E)/501(E) 2025) and SMPV ame | PESO gazette PDFs | R-033 VERIFIED_CONDITIONAL; R-034 ROC; LPG UNKNOWN |
| UR-11 | OPEN (carried from v4) | Notified licensing officer and forms | State notification under Insecticides Act s.13 / FDA Maharas | Authority CONDITIONAL; UNK-036 open |
| UR-12 | OPEN | Final MH OSH rules | Gazette (only drafts of 06-05-2026 listed) | DRAFT labels retained |
| UR-13 | OPEN | MAITRI per-service integration evidence | MAITRI service specs/API docs | INTEGRATION_STATUS UNKNOWN |
| UR-14 | CLOSED_AS_SITE_DEPENDENT | Zone permissibility is decided per planning authority and site | - | R-105 INSUFFICIENT_DATA until 4 inputs; then CONDITIONAL |
| UR-15 | PARTIAL | Currency of MWRRA order 31-07-2015 and complete village list; final Ru | MWRRA confirmation / later orders | R-097 REQUIRES_CONFIRMATION; unmatched village -> INSUFFICIENT_DATA |
| UR-16 | CLOSED | Per-column cells read from clean vector pages (mfs_annexA_cells) | - | Cells VERIFIED_CONDITIONAL; note 12 overlay with Annexure A-1 |
| UR-17 | OPEN | Per-site competent authority | Site facts / notifications | authority_status REQUIRES_CONFIRMATION; never defaulted (no MSEDCL def |
| UR-18 | OPEN | Clock-start event; category scope | MPCB clarification; central gazette 84(E)/85(E) as amended | SLA-001..003 shown as ADMINISTRATIVE working days; clock start UNKNOWN |
| UR-19 | OPEN | MIDC DCR text | MIDC DCPR / regulations gazette | REQUIRES_CONFIRMATION (portal only) |

## 16. Final implementation-safe rule count

**76** rules (the list file has 83 rows including MSIHC and EPR records).

## 17. Final requires-confirmation count

**26** rules (the list file has 52 rows).

## 18. Final DNI count

**3** rules (the list file has 24 rows).

## 19. Automated validation results

| check | description | result | evidence |
|---|---|---|---|
| CHECK 01 | Every deterministic rule has a resolvable source_id | PASS | 96 deterministic rules; missing [] |
| CHECK 02 | Every threshold has a locator (rules + peso_thresholds + mfs cells) | PASS | missing [] |
| CHECK 03 | Every MSIHC threshold has a locator | PASS | 221 rows; missing [] |
| CHECK 04 | Every timeline typed LEGAL / RTS/SERVICE / ADMINISTRATIVE / PORTAL | PASS | sla Counter({'LEGAL': 18, 'RTS/SERVICE': 13, 'PORTAL': 13, 'ADMINISTRATIVE': 6}); MIDC RTS legal/portal separated=True;  |
| CHECK 05 | No portal/T3+ source is the sole proof of a deterministic legal rule | PASS | violations []; guards/routing exempt ['R-015', 'R-035', 'R-047', 'R-059', 'R-074']; R-036/R-037 downgraded |
| CHECK 06 | Authorities verified or explicitly marked unresolved | PASS | {'VERIFIED': 15, 'REQUIRES_CONFIRMATION': 7}; unresolved listed in UR-17 |
| CHECK 07 | Draft/superseded never treated as current | PASS | draft sources ['SRC-118', 'SRC-172', 'SRC-176'] - none sole basis of a safe rule; MH OSH rules DRAFT; MSIHC v3 table SUP |
| CHECK 08 | DNI never enters orchestration (safe list clean) | PASS | leaks []; misclassified [] |
| CHECK 09 | UNKNOWN never becomes DOES_NOT_APPLY/FALSE (text scan) | PASS | hits [] |
| CHECK 10 | All conflicts recorded with sources, dates, legal status, resolution, status | PASS | 28 conflicts; incomplete [] |
| CHECK 11 | Incentive amounts blocked | PASS | 14 components; R-059 NOT_COMPUTED |
| CHECK 12 | MSIHC values pass locator + effective-date validation | PASS | VERIFIED 218; check violations []; missing date/locator [] |
| CHECK 13 | General fire renewal separate from sector-specific certificate | PASS | classes ['CLAIMED_EXCEPTION', 'GENERAL_FIRE_APPROVAL', 'SECTOR_SPECIFIC_CERTIFICATE'] |
| CHECK 14 | EPR is role-driven | PASS | 13 role rows; generic manufacturer -> INSUFFICIENT_DATA |
| CHECK 15 | Planning requires authority + site facts | PASS | R-105 inputs planning_authority, zone, proposed_use, existing_use |
| CHECK 16 | Effective-date status on every rule (temporal answer or INSUFFICIENT_DATA) | PASS | Counter({'EXACT_DATE': 61, 'YEAR_ONLY': 25, 'UNKNOWN': 19}) |
| CHECK 17 | Integration claims need evidence; no NO_INTEGRATION | PASS | claims Counter({'UNKNOWN': 5, 'VERIFIED_CONDITIONAL': 1}); NO_INTEGRATION hits [] |
| CHECK 18 | Every source id resolves | PASS | 188 sources; unresolved [] |
| CHECK 19 | Counts generated from data | PASS | report5 and summary JSON compute every count from the tables at build time |
| CHECK 20 | Every unresolved item has reason, missing evidence, next evidence, engine behaviour | PASS | 19 items; incomplete [] |

### Target detail: MPCB timeline matrix

| row | category | consent | central (LEGAL) | MPCB (ADMIN, working days) | clock start | status |
|---|---|---|---|---|---|---|
| MCT-G-CTE | Green | CTE | 30 | 15 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-G-CTO | Green | CTO | 30 | 15 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-G-Renewal | Green | Renewal | 30 | 15 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-O-CTE | Orange | CTE | 45 | 24 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-O-CTO | Orange | CTO | 60 | 24 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-O-Renewal | Orange | Renewal | 60 | 24 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-R-CTE | Red | CTE | 60 | 40 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-R-CTO | Red | CTO | 90 | 40 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-R-Renewal | Red | Renewal | 120 | 40 | UNKNOWN | VERIFIED_CONDITIONAL |
| MCT-X-9 | Blue / White / other | any | see SLA-036 (expansion) / UNKNOWN | NOT ADDRESSED | UNKNOWN | UNKNOWN |
| MCT-X-10 | any | Expansion / amendment consent | see SLA-036 (expansion) / UNKNOWN | NOT ADDRESSED | UNKNOWN | UNKNOWN |

### Target detail: MSIHC audit of the 20 v4 REQUIRES_OFFICIAL_CONFIRMATION rows

| entry | chemical | col 3 | col 4 | v5 outcome | effective |
|---|---|---|---|---|---|
| S1-TOX | Toxic classes | Extremely toxic / highly  | - | REQUIRES_OFFICIAL_CONFIRMATION | 2000-01-20 |
| S2-12 | Carbonyl chloride | 0.750 t | 0.750 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-13 | Hydrogen sulphide | 5 t | 50 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-14 | Hydrogen fluoride | 5 t | 50 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-15 | Hydrogen cyanide | 5 t | 50 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-16 | Carbon disulphide | 20 t | 200 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-17 | Bromine | 50 t | 500 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-18 | Ethylene oxide | 5 t | '501' as printed (probabl | VERIFIED_CONDITIONAL (col 3 verified; col 4 REQUIRES_OFFICIAL_CONFIRMATION) | 1994-10-03 |
| S2-19 | Propylene oxide | 5 t | 50 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-20 | Acrolein | 20 t | 200 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-21 | Methyl bromide | 20 t | 200 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-22 | Methyl isocyanate | 0.150 t | 0.150 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-23 | Tetraethyl lead or tetramethyl lead | 5 t | 50 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-24 | 1,2-Dibromoethane (Ethylene dibromi | 5 t | 50 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-25 | Hydrogen chloride (liquefied gas) | 25 t | 250 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-26 | Diphenyl methane di-isocyanate (MDI | 20 t | 200 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S2-27 | Toluene di-isocyanate (TDI) | 10 t | 100 t | VERIFIED_T1_CONSOLIDATED | 1994-10-03 |
| S3P1-049 | 4-Fluorocrotonic acid (gazette name | 1 kg | NOT_PRINTED | VERIFIED_PRIMARY_GAZETTE | 1989-11-27 |
| S3P1-099 | Warfarin | 100 kg | NOT_PRINTED | VERIFIED_PRIMARY_GAZETTE | 1989-11-27 |
| S3P1-111 | Ethyleneimine | 5 t | NOT_PRINTED | REQUIRES_OFFICIAL_CONFIRMATION | 1989-11-27 |

### Target detail: PESO thresholds

| id | item | qty | unit | consequence | rule | status |
|---|---|---|---|---|---|---|
| PT-01 | Compressed gas cylinders - flammable non-toxi | 25 cylinders OR 200 kg (whichever less) | cylinders / kg | No licence (r.44(b)(i)); above -> Form E/F licence | GCR r.44(b)(i) | VERIFIED_CONDITIONAL |
| PT-02 | Non-flammable non-toxic gas cylinders (own us | 200 | cylinders | No licence (r.44(b)(ii)) | GCR r.44(b)(ii) | VERIFIED_CONDITIONAL |
| PT-03 | Toxic gas cylinders (own use) | 5 | cylinders | No licence (r.44(b)(iii)) | GCR r.44(b)(iii) | VERIFIED_CONDITIONAL |
| PT-04 | Dissolved acetylene cylinders (own use) | 25 | cylinders | No licence (r.44(b)(iv)) | GCR r.44(b)(iv) | VERIFIED_CONDITIONAL |
| PT-05 | LPG (r.44(c)) | 100 | kg | UNKNOWN | GCR r.44(c) | UNKNOWN |
| PT-06 | Form F storage for sale/trading; Form G CNG - | - | - | DA NOC required (r.48) | GCR r.48(1)-(3); G.S.R.315(E) | VERIFIED_CONDITIONAL |
| PT-07 | Pressure vessel (SMPV) | 1000 | litres water capacity | Storage licence LS-1A/LS-1B (r.45) | SMPV r.2(ix), r.2(xxxvii), r.45 | REQUIRES_OFFICIAL_CONFIRMATION |
| PT-08 | SMPV processing-plant exemption | 16 | hours of gas feed requirement | Rules not applicable to such vessels (as printed) | SMPV r.3 | REQUIRES_OFFICIAL_CONFIRMATION |
| PT-09 | SMPV large storage siting | 50 t or 100 m3 | tonnes / m3 | 500 m surroundings + HAZOP in plan (vs 100 m other | SMPV r.46(1)(i)(c) | REQUIRES_OFFICIAL_CONFIRMATION |
| PT-10 | SMPV District Authority NOC | - | - | NOC required before 05-06-2026; OMITTED from 05-06 | SMPV r.47; G.S.R.448(E) rule 4 | VERIFIED |
| PT-11 | Petroleum licence validity | 3 | years (max) | Renewal (r.148) | Petroleum Rules r.142(2), r.148 | VERIFIED_CONDITIONAL |
| PT-12 | GCR licence validity (E/F/G) | 10 | years (max) | Renewal (r.55) | GCR r.51(2), r.55(2) | VERIFIED_CONDITIONAL |
| PT-13 | SMPV licence validity (LS-1A/1B) | 5 | years (max) | Renewal (r.55) | SMPV r.51(1), r.55(2) | VERIFIED_CONDITIONAL |
| PT-14 | Petroleum Class A small-quantity exemption (S | 30 | litres | DO NOT IMPLEMENT (CON-014) | none in T1 | DO_NOT_IMPLEMENT_YET |

### Target detail: general vs sector-specific certificates

| id | class | certificate | renewal | engine | status |
|---|---|---|---|---|---|
| SSC-01 | SECTOR_SPECIFIC_CERTIFICATE | PESO licence under Petroleum Rules 2002 (other tha | Renewable by licensing authority for 3 calendar years where  | APPLIES if unit holds such a licence (input); VERIFIED_CONDI | VERIFIED_CONDITIONAL |
| SSC-02 | SECTOR_SPECIFIC_CERTIFICATE | PESO licence Form E/F/G under Gas Cylinders Rules  | Renewal up to 10 years (r.55(2)) | APPLIES if licence held; amendments 386(E)/839(E)/315(E) rea | VERIFIED_CONDITIONAL |
| SSC-03 | SECTOR_SPECIFIC_CERTIFICATE | PESO licence LS-1A/LS-1B under SMPV(U) Rules 2016 | Renewal up to 5 years (r.55(2)) | APPLIES if licence held; 2018/2019/2021 amendments not read | VERIFIED_CONDITIONAL |
| SSC-04 | GENERAL_FIRE_APPROVAL | Renewal of Final Fire Safety Approval (MFS) | No renewal of final approval (Form B twice yearly is separat | DOES_NOT_APPLY (FR-01) unless another Act/Rule requires it ( | VERIFIED |
| SSC-05 | CLAIMED_EXCEPTION | MFS PA-7 claim: Petroleum Act / Gas Cylinder Rules | NOT_FOUND in Petroleum Rules 2002, GCR 2016, SMPV 2016 texts | F-FIR-20 stays UNKNOWN unless a rule is cited; PESO licence  | REQUIRES_OFFICIAL_CONFIRMATION |

### Target detail: EPR role screening

| id | regime | role | applicability | duty | status |
|---|---|---|---|---|---|
| EPRS-01 | Plastic packaging (PWM) | producer / importer / brand owner (PIBO) | CONDITIONAL on role; role UNKNOWN -> INSUFFICIENT_ | Annual EPR targets per Schedule II | VERIFIED_CONDITIONAL |
| EPRS-02 | Plastic packaging (PWM) | plastic waste processor / seller of plastic raw ma | CONDITIONAL on role | Registration + returns | VERIFIED_CONDITIONAL |
| EPRS-03 | Battery (BWM) | producer (manufacturer / own-brand seller / import | CONDITIONAL on role | EPR targets; marking incl. EPR reg. no. via barcod | VERIFIED_CONDITIONAL |
| EPRS-04 | Battery (BWM) | refurbisher / recycler | CONDITIONAL on role | Registration + returns (detail not extracted) | REQUIRES_OFFICIAL_CONFIRMATION |
| EPRS-05 | E-waste | bulk consumer | CONDITIONAL (R-094); UNKNOWN -> INSUFFICIENT_DATA | Hand over e-waste only to registered producer/refu | VERIFIED_CONDITIONAL |
| EPRS-06 | E-waste | producer / manufacturer / refurbisher / recycler | CONDITIONAL on role | Registration + EPR (not modelled) | REQUIRES_OFFICIAL_CONFIRMATION |
| EPRS-07 | Used oil | producer of base oil / lubricating oil; importer o | CONDITIONAL on role | EPR certificates from registered recyclers | REQUIRES_OFFICIAL_CONFIRMATION |
| EPRS-08 | Used oil | recycler / collection agent | CONDITIONAL on role | Registration | REQUIRES_OFFICIAL_CONFIRMATION |
| EPRS-09 | Waste tyre | producer (6 limbs) | CONDITIONAL on role | EPR obligation; quarterly returns; certificates | VERIFIED_CONDITIONAL |
| EPRS-10 | Waste tyre | recycler / retreader | CONDITIONAL on role | Registration; monthly information (recycler) | VERIFIED_CONDITIONAL |
| EPRS-11 | Non-ferrous scrap | producer / importer of used devices or scrap | CONDITIONAL on role | Registration (r.52); EPR per Sch XI | VERIFIED_CONDITIONAL |
| EPRS-12 | Non-ferrous scrap | manufacturer / collection agent / refurbisher / re | CONDITIONAL on role | Registration (r.45); recycler duties (r.55) | VERIFIED_CONDITIONAL |
| EPRS-13 | ALL | synthetic organic chemical manufacturer (no role f | INSUFFICIENT_DATA - chemical manufacturing alone n | - | VERIFIED |

### Target detail: MFS Annexure A cells (UR-16)

| band | extinguisher | hose_reel | dry_riser | wet_riser | down_comer | yard_hydrant | sprinkler | manual_alarm | auto_detection | ug_tank_L | terrace_tank_L | pump_near_ug_lpm | terrace_pump_lpm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G-1 <=500 m2 built-up area | R | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR | NR |
| G-1 >500-1000 m2 built-up area | R | NR | NR | NR | NR | NR | NR | NR | NR | NR | 5000 | NR | NR |
| G-1 >1000-2000 m2 built-up area | R | R | NR | NR | NR | NR | NR | NR | NR | NR | 10000 | NR | 180 |
| G-1 >2000-3000 m2 built-up area | R | R | NR | R | R | NR | R(note1) | R | NR | 15000(5000;note4) | 5000 | 450 | 180 |
| G-1 >3000-5000 m2 built-up area | R | R | NR | R | R | R | R(note1) | R | R | 40000(10000;note4) | 10000(5000;note4) | 900(note7) | 450 |
| G-1 >5000 m2 built-up area | R | R | NR | R | R | R | R(note1) | R | R | 50000(10000;note4) | 10000(5000;note4) | 1620(note8) | 900 |
| G-2 <=500 m2 built-up area | R | R | NR | NR | R | NR | R(note1) | NR | NR | NR | 5000(5000;notes1,2,4,5) | NR | 180 |
| G-2 >500-1000 m2 built-up area | R | R | NR | NR | R | NR | R(note1) | NR | NR | 20000(5000;note4) | 10000(5000;notes1,2,4,5) | 600(note6) | 180 |
| G-2 >1000-3000 m2 built-up area | R | R | NR | R | R | R | R(note1) | R | NR | 30000(5000;note4) | 10000(5000;notes1,2,4,5) | 900(note7) | 450 |
| G-2 >3000-5000 m2 built-up area | R | R | NR | R | R | R | R(note1) | R | R | 40000(10000;note4) | 10000(5000;notes1,2,4,5) | 1620(note8) | 450 |
| G-2 >5000 m2 built-up area | R | R | NR | R | R | R | R | R | R | 60000(10000;note4) | 10000(5000;notes1,2,4,5) | 2280(note9) | 450 |
| G-3 <=500 m2 built-up area | R | R | NR | R | R | NR | R(note1) | NR | NR | 20000(5000;note4) | 5000(5000;notes1,2,4,5) | 450(note7) | 180(notes1,2,4,5) |
| G-3 >500-1000 m2 built-up area | R | R | NR | R | R | R | R(note1) | NR | R | 50000(5000;note4) | 10000(5000;notes1,2,4,5) | 1620(note8) | 450(notes1,2,4,5) |
| G-3 >1000-3000 m2 built-up area | R | R | NR | R | R | R | R | NR | R | 100000 | 20000(5000;notes1,2,4,5) | 2280(note9) | 900(notes1,2,4,5) |
| G-3 >3000 m2 built-up area | R | R | R | R | R | R | R | R | R | 150000 | 20000(5000;notes1,2,4,5) | 2850(note10) | 900(notes1,2,4,5) |

Values in brackets are the additional quantity under the cited note. Note 4 adds it where the basement exceeds 200 m², the floor plate exceeds 1,125 m², or the height is 15 m or more. Under note 5, the terrace quantity is added to the underground tank where no overhead tank is possible. Note 12 applies Annexure A-1 areas to sprinklers and detection. Installation counts are not derived.

## 20. Changelog

`csv/changelog_v5.csv` has 591 rows, with columns CHANGE_ID, TABLE, RECORD_ID, FIELD, OLD_VALUE, NEW_VALUE, REASON, SOURCE_ID, EXACT_LOCATOR, SOURCE_TIER, PUBLICATION_DATE, EFFECTIVE_DATE, CONFIDENCE, IMPLEMENTATION_STATUS and change_type. By type: ADDITION 73, CORRECTION 456, LIST_ADD 17, LIST_REMOVE 32, NEW_TABLE 13. The v2–v4 changelogs are carried over unchanged. Changes by table:

| table | changes |
|---|---|
| msihc_t1_thresholds | 160 |
| sla | 71 |
| unresolved_items | 71 |
| closure_matrix | 44 |
| sources | 32 |
| requires_confirmation | 31 |
| rules | 29 |
| edge_tests | 28 |
| epr_regimes | 23 |
| authorities | 22 |
| mfs_industrial_order | 16 |
| implementation_safe_rules | 16 |
| conflicts | 11 |
| peso_gating | 7 |
| groundwater_regulator_matrix | 5 |
| facts | 3 |
| dsb_workflow | 3 |
| planning_steps | 2 |
| do_not_implement | 2 |
| mpcb_consent_timeline_2026 | 1 |
| msihc_amendment_chain | 1 |
| msihc_value_chronology | 1 |
| sector_specific_certificates | 1 |
| fire_renewal_model | 1 |
| peso_thresholds | 1 |
| mfs_annexA_cells | 1 |
| epr_role_screening | 1 |
| labour_classification | 1 |
| maitri_integration_claims | 1 |
| engine_state_contract | 1 |
| rule_register_v5 | 1 |
| automated_checks | 1 |
| readiness_abcd | 1 |
| machine_summary_v5 | 1 |

## Machine-readable summary

```json
{
 "IMPLEMENTATION_SAFE_RULES": 76,
 "REQUIRES_CONFIRMATION_RULES": 26,
 "DO_NOT_IMPLEMENT_RULES": 3,
 "UNKNOWN_RULES": 3,
 "UNKNOWN_RULE_IDS": [
  "R-015",
  "R-052",
  "R-074"
 ],
 "CONFLICTS": 28,
 "UNRESOLVED_ITEMS": 17,
 "SOURCE_COUNT": 188,
 "PRIMARY_SOURCE_COUNT": 70,
 "SECONDARY_SOURCE_COUNT": 118,
 "SOURCE_TIERS": {
  "T1": 70,
  "T2": 31,
  "T3": 67,
  "T4": 9,
  "T5": 11
 },
 "LIST_ROWS": {
  "implementation_safe": 83,
  "requires_confirmation": 52,
  "do_not_implement": 24
 },
 "ACTIVE_RULES": 105,
 "CHECKS": {
  "PASS": 20
 },
 "V5_CHANGES": 591
}
```
