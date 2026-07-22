# Gold Audit — LLM (Claude Fable 5) Review — NOT the human audit

**Provenance disclaimer (read first).** These verdicts were produced by
Claude Fable 5 on 2026-07-21, judging each span against the inline context
in `gold_audit.md`. The model identity key (`gold_audit.key.json`) was NOT
opened. This file must not be reported as the paper's blind human audit:
the gold originates from a Claude model, so a Claude-family judge shares
potential family blind spots — exactly the circularity RQ1 quantifies. Use
this as (a) a triage to shrink the human pass, and (b) a later
human-vs-LLM agreement measurement once the human verdicts exist.

**Rubric applied.**
- Y = label correctly describes the span; punctuation-only raggedness
  (brackets, trailing comma/period/colon, quotes, parens) does not void a Y.
- N = wrong label type, generic/non-entity phrase, code/log/page-furniture
  token, OR span includes extra *words* beyond the entity, OR span is a
  fragment of the entity (e.g. half of a line-split hash).
- conf=low marks judgment calls a human should adjudicate (51 items —
  grep `| low |`). conf=high items are intended to be skimmable.

| item_id | predicted_label | verdict | conf | note |
|---|---|---|---|---|
| A000 | file name | Y | high | HRsword.exe |
| A001 | attack technique id | Y | high | T1027; punctuation only |
| A002 | file hash | N | high | Python code fragment |
| A003 | file hash | N | low | 14-hex fragment of line-split SHA-256 |
| A004 | file name | N | low | file extension (.vmsn), not a name |
| A005 | hacking tool | N | high | fragment of technique title "Ingress Tool Transfer" |
| A006 | cwe identifier | N | high | span is T1219 + footnote refs; wrong type |
| A007 | malware family | Y | high | Snake |
| A008 | affected software product | Y | high | Ivanti ZTA Gateways |
| A009 | yara rule name | N | high | "ustart" is Snake protocol token |
| A010 | threat actor group | N | high | generic "threat actors'" |
| A011 | tlp classification | N | low | span includes "CISA"; TLP:CLEAR alone correct |
| A012 | file hash | N | low | 50-hex first half of line-split SHA-256 |
| A013 | ip address | N | high | literal column word "Ipv4" |
| A014 | attack technique name | N | high | MOVEit Transfer is a product; wrong type |
| A015 | tactic | N | high | Lateral Tool Transfer is a technique (T1570) |
| A016 | malware family | Y | high | Snake |
| A017 | malware family | N | high | page furniture ("Page") |
| A018 | ip address | N | high | generic phrase "IP address" |
| A019 | email address | N | high | phone number |
| A020 | email address | Y | low | defanged email; span carries markup artifact |
| A021 | affected software product | Y | high | SimpleHelp |
| A022 | tactic | Y | high | Exfiltration (TA0010) table header |
| A023 | malware family | N | high | page furniture |
| A024 | attack technique name | N | high | generic "ransomware techniques" |
| A025 | attack technique name | Y | high | Shared Modules (T1129) |
| A026 | affected software product | Y | high | SimpleHelp RMM |
| A027 | ip address | N | high | literal "Ipv4" |
| A028 | threat actor group | Y | high | NoName057(16) |
| A029 | attack technique name | N | low | fragment/typo of "Exploitation of Remote Services" (T1210) |
| A030 | malware family | Y | high | Snake |
| A031 | tactic | N | high | mitigation concept, not ATT&CK tactic |
| A032 | cve identifier | Y | high | CVE-2023-34362 |
| A033 | attack technique name | N | high | framework name "ATT&CK" |
| A034 | affected software product | Y | high | FortiOS |
| A035 | cwe identifier | Y | high | CWE-89; punctuation only |
| A036 | email address | N | high | phone number |
| A037 | ip address | N | high | literal "Ipv4" |
| A038 | tlp classification | Y | high | TLP:CLEAR |
| A039 | attack technique id | Y | high | T1110.003 |
| A040 | tactic | Y | high | Defense Evasion |
| A041 | attack technique id | Y | high | T1070.001 |
| A042 | cve identifier | Y | high | CVE-2023-34362 |
| A043 | attack technique id | Y | high | T0812 |
| A044 | affected software product | Y | low | OS name; "affected" reading weak in mitigation context |
| A045 | file name | N | low | file extension (.vswp) |
| A046 | file path | Y | high | /gsb/reports[.]php (defanged) |
| A047 | file hash | N | high | code fragment |
| A048 | file name | Y | low | "Comadmin" names the file; canonical comadmin.dat |
| A049 | file hash | N | low | 50-hex first half of split SHA-256 |
| A050 | cve identifier | Y | high | CVE-2024-9379 |
| A051 | tactic | N | high | generic acronym "TTPs" |
| A052 | file name | N | low | YARA string constant, not a file name |
| A053 | file hash | N | low | 16-hex tail of three-way-split SHA-256 |
| A054 | attack technique name | Y | high | Screen Capture (T1113) |
| A055 | attack technique name | N | high | Snake "Passive method", not ATT&CK |
| A056 | tlp classification | Y | high | TLP:CLEAR |
| A057 | file path | N | high | code fragment |
| A058 | ip address | N | high | generic phrase |
| A059 | attack technique id | Y | high | T1036 |
| A060 | malware family | Y | high | Snake |
| A061 | tlp classification | Y | high | TLP:CLEAR |
| A062 | file path | N | low | "1.yar" is a bare file name; type boundary |
| A063 | tlp classification | Y | high | TLP:CLEAR |
| A064 | affected software product | N | low | WinSCP used as actor tool here; product/tool boundary |
| A065 | hacking tool | N | low | Snake; malware family per gold convention |
| A066 | malware family | Y | high | Snake |
| A067 | yara rule name | N | high | Suricata rule msg string |
| A068 | file path | N | high | username token |
| A069 | tactic | N | high | technique title (T0840), not tactic |
| A070 | attack technique name | N | high | generic "ATT&CK techniques" |
| A071 | email address | N | high | code fragment |
| A072 | yara rule name | N | high | advisory ID |
| A073 | hacking tool | N | high | Python import token |
| A074 | cwe identifier | Y | high | CWE-22 |
| A075 | threat actor group | Y | high | APT44 |
| A076 | file path | N | high | code fragment |
| A077 | file path | N | high | log token "sudo:" |
| A078 | ip address | N | high | literal "Ipv4" |
| A079 | tlp classification | Y | high | TLP:CLEAR |
| A080 | file path | N | high | code fragment |
| A081 | file name | N | low | WerFaultSvc is a service name, not a file |
| A082 | cve identifier | Y | high | CVE-2024-8963 |
| A083 | tlp classification | Y | high | TLP:CLEAR |
| A084 | ip address | N | high | literal "Ipv4" |
| A085 | file hash | N | low | 31-hex fragment of split MD5 |
| A086 | tlp classification | Y | high | TLP:CLEAR |
| A087 | cve identifier | Y | high | CVE-2024-9380 |
| A088 | email address | N | high | code fragment |
| A089 | malware family | N | high | YARA metadata string "ransomware" |
| A090 | tactic | N | high | generic; technique-level at best |
| A091 | hacking tool | Y | low | PowerShell in actor-leveraged-tools table; canonical dual-use call |
| A092 | file path | Y | high | /dev/urandom |
| A093 | tlp classification | Y | high | TLP:CLEAR |
| A094 | yara rule name | Y | high | rule GRXBA declaration |
| A095 | tactic | Y | high | Command and Control |
| A096 | cve identifier | Y | high | CVE-2024-9380 |
| A097 | email address | Y | high | defanged gmail |
| A098 | attack technique id | Y | high | T1140 |
| A099 | file name | N | low | descriptive role ("Snake Queue File"), not literal name |
| A100 | threat actor group | N | high | LummaC2 is malware |
| A101 | file hash | N | high | code fragment |
| A102 | cve identifier | Y | low | CVE-2024-8963 plus footnote markers in span |
| A103 | file name | N | high | SQL alias |
| A104 | malware family | N | high | page furniture |
| A105 | tlp classification | N | low | "TLP:" fragment of split "TLP: CLEAR" |
| A106 | threat actor group | Y | high | TA505 |
| A107 | file name | Y | high | Usysdiag.exe |
| A108 | file path | N | high | code fragment |
| A109 | attack technique id | N | high | TLP marking |
| A110 | affected software product | Y | high | Ivanti CSA |
| A111 | attack technique name | N | high | generic phrase |
| A112 | threat actor group | N | low | span "CL0P actors"; group name is CL0P alone |
| A113 | malware family | N | high | page furniture |
| A114 | threat actor group | Y | high | CARR |
| A115 | file hash | Y | high | full SHA-256 |
| A116 | affected software product | Y | high | Ivanti CSA |
| A117 | cve identifier | Y | high | CVE-2022-41040 |
| A118 | tactic | Y | high | Persistence |
| A119 | affected software product | Y | high | Ivanti Policy Secure |
| A120 | malware family | Y | high | SNAKE (section header mention) |
| A121 | cve identifier | Y | high | CVE-2023-0669 |
| A122 | threat actor group | N | high | Snake is malware |
| A123 | file name | N | low | file extension (.nvram) |
| A124 | threat actor group | Y | high | CL0P |
| A125 | cve identifier | Y | high | CVE-2024-8963 |
| A126 | malware family | Y | high | LummaC2 |
| A127 | tactic | N | high | TLP marking |
| A128 | yara rule name | N | high | page-furniture "CLEAR" |
| A129 | attack technique name | N | low | "Phishing:" fragment of subtechnique title |
| A130 | threat actor group | Y | high | Sector16 |
| A131 | hacking tool | N | low | Tor as network infrastructure here |
| A132 | ip address | N | high | generic phrase |
| A133 | tactic | N | high | generic "(TTPs)" |
| A134 | attack technique name | Y | low | "SQL injection": generic technique vs ATT&CK-title schema question |
| A135 | hacking tool | N | high | username token |
| A136 | tlp classification | Y | high | TLP:CLEAR |
| A137 | attack technique id | Y | high | T1570 |
| A138 | email address | N | high | code fragment |
| A139 | yara rule name | N | high | Suricata msg |
| A140 | file path | N | high | generic "typical path" |
| A141 | file path | N | high | username token |
| A142 | hacking tool | N | low | psql: legitimate utility inside attacker code |
| A143 | cve identifier | N | high | TLP marking |
| A144 | email address | Y | high | report@cisa.gov |
| A145 | tlp classification | N | high | "Role:" token |
| A146 | threat actor group | Y | high | NoName057(16) |
| A147 | malware family | Y | high | "Snake" |
| A148 | attack technique id | Y | high | T1572 |
| A149 | attack technique name | Y | high | Lateral Tool Transfer |
| A150 | email address | Y | high | contact@cisa.dhs.gov |
| A151 | ip address | N | high | container id 0x3 |
| A152 | threat actor group | N | high | generic "Threat actors" |
| A153 | threat actor group | Y | high | CL0P |
| A154 | attack technique id | Y | high | T1564.002 |
| A155 | file name | N | low | path-like URL string; name/path boundary |
| A156 | threat actor group | N | low | "FSB operators"; FSB alone arguably the group |
| A157 | hacking tool | N | low | Snake; malware family per gold convention |
| A158 | tlp classification | N | low | "CLEAR" fragment of split marking |
| A159 | affected software product | Y | high | SimpleHelp |
| A160 | ip address | N | high | generic phrase |
| A161 | attack technique id | N | high | TLP marking |
| A162 | file hash | N | high | variable name |
| A163 | file hash | N | low | 14-hex tail of split hash |
| A164 | file name | Y | high | "1.yar" |
| A165 | file path | N | high | username token |
| A166 | file hash | Y | high | full SHA-256 |
| A167 | yara rule name | Y | high | PlayForESXi |
| A168 | file hash | N | high | SQL column name |
| A169 | tactic | N | high | generic lowercase "impact" |
| A170 | attack technique id | Y | high | T1190 |
| A171 | file hash | Y | high | quoted MD5 |
| A172 | attack technique id | Y | high | T1190 |
| A173 | hacking tool | N | high | log token "sudo:" |
| A174 | hacking tool | Y | high | Obelisk scanner |
| A175 | cve identifier | N | high | advisory ID |
| A176 | yara rule name | N | high | UNIX find command |
| A177 | tlp classification | Y | high | TLP:CLEAR |
| A178 | email address | Y | high | Report@cisa.gov |
| A179 | file name | Y | high | LummaC2.exe; paren only |
| A180 | yara rule name | N | low | this mention names the infostealer, not the rule |
| A181 | file path | N | high | code fragment |
| A182 | email address | N | high | protocol name SMTP |
| A183 | attack technique name | N | low | generic lowercase "phishing" usage |
| A184 | yara rule name | N | high | Suricata msg |
| A185 | attack technique name | N | high | descriptive phrase |
| A186 | tlp classification | Y | high | TLP:CLEAR |
| A187 | hacking tool | N | low | psql (same class as A142) |
| A188 | attack technique id | Y | high | T0840 |
| A189 | email address | Y | high | report@cisa.gov |
| A190 | file hash | Y | high | quoted MD5 |
| A191 | attack technique id | Y | high | T1046 |
| A192 | tlp classification | Y | high | TLP:CLEAR |
| A193 | cve identifier | Y | high | CVE-2024-9379 |
| A194 | attack technique name | Y | high | Application Shimming (T1546.011) |
| A195 | cwe identifier | N | high | advisory ID |
| A196 | threat actor group | Y | high | CL0P's (possessive) |
| A197 | email address | N | high | TLP marking |
| A198 | tlp classification | Y | high | TLP:CLEAR |
| A199 | email address | N | high | phone number |
| A200 | hacking tool | Y | high | Plink |
| A201 | tactic | Y | high | Lateral Movement |
| A202 | file hash | Y | high | full SHA-256 |
| A203 | attack technique id | N | low | TA0010 is a tactic ID, not a technique ID |
| A204 | tactic | N | high | Masquerading is a technique title |
| A205 | cve identifier | Y | high | CVE-2022-41040 |
| A206 | tlp classification | N | low | "TLP:" fragment |
| A207 | cwe identifier | Y | high | CWE-77 |
| A208 | attack technique id | Y | high | T1104 |
| A209 | file name | N | low | HRsword here names the tool, not a file |
| A210 | file path | N | low | CAService.exe is a bare file name |
| A211 | tactic | Y | high | Defense Evasion |
| A212 | tactic | N | high | TLP marking |
| A213 | email address | Y | high | report@cisa.gov |
| A214 | tactic | N | high | generic "common tactics," |
| A215 | file path | N | high | code string |
| A216 | file name | N | high | SQL column |
| A217 | file name | Y | high | jpsetup.exe |
| A218 | attack technique name | N | high | Snake ops mode |
| A219 | cve identifier | N | high | advisory ID |
| A220 | tactic | N | low | tail of technique title "Service Execution" (T1569.002) |
| A221 | malware family | N | high | page furniture |
| A222 | yara rule name | N | high | generic "YARA rules." |
| A223 | file path | N | high | code fragment |
| A224 | file hash | N | high | SQL column "core," |
| A225 | file name | Y | high | Werfault.exe |
| A226 | cve identifier | Y | high | CVE-2024-8963 |
| A227 | tactic | Y | high | Persistence |
| A228 | attack technique id | Y | high | T1001 |
| A229 | hacking tool | N | low | DEWMODE web shell; malware family arguably |
| A230 | malware family | Y | high | FlawedGrace |
| A231 | file name | N | low | file extension (.vmsd) |
| A232 | threat actor group | N | high | Snake is malware |
| A233 | malware family | N | high | page furniture |
| A234 | cwe identifier | Y | high | CWE-78 |
| A235 | file hash | Y | high | 40-hex; doc's "MD5" caption wrong but label correct |
| A236 | file path | N | high | SQL column |
| A237 | cve identifier | Y | high | CVE-2025-0282 |
| A238 | cve identifier | Y | high | CVE-2018-13379 |
| A239 | ip address | N | high | literal "Ipv4" |
| A240 | file name | Y | low | GUID.GUID.crmlog template pattern, not literal name |
| A241 | cve identifier | Y | high | CVE-2023-34362 |
| A242 | malware family | Y | high | Play |
| A243 | email address | N | high | URL |
| A244 | attack technique id | Y | high | T1190 |
| A245 | tactic | N | high | fragment of subtechnique title |
| A246 | yara rule name | N | high | ustart |
| A247 | affected software product | Y | low | product named; context is config guidance, not compromise |
| A248 | file path | N | high | username token |
| A249 | tlp classification | Y | high | TLP:CLEAR |
| A250 | email address | Y | high | Report@cisa.gov |
| A251 | hacking tool | N | low | ComRAT is an implant; malware family arguably |
| A252 | cve identifier | Y | high | CVE-2024-9379 |
| A253 | yara rule name | Y | high | CISA_10450442_01 |
| A254 | hacking tool | N | high | log token "sudo:" |
| A255 | threat actor group | Y | high | Turla |
| A256 | attack technique name | N | high | Snake ops mode fragment |
| A257 | yara rule name | N | high | ustart |
| A258 | hacking tool | N | high | code fragment |
| A259 | file hash | N | high | variable "p" |
| A260 | tactic | N | high | generic lowercase "execution." |
| A261 | email address | N | high | code fragment |
| A262 | malware family | Y | high | Snake |
| A263 | file path | N | high | log token "sudo:" |
| A264 | hacking tool | N | high | "Stage 2" descriptor |
| A265 | hacking tool | N | low | Volatility used defensively in context |
| A266 | hacking tool | N | high | code fragment |
| A267 | yara rule name | N | low | "Grixba:" names the tool; rule name is GRXBA |
| A268 | tlp classification | Y | high | TLP:CLEAR |
| A269 | file path | N | high | username token |
| A270 | threat actor group | N | high | generic descriptor + leaked annotation markup in context |
| A271 | file hash | N | high | code fragment |
| A272 | attack technique name | N | low | "Remote Services:" prefix of subtechnique row; T1021 title arguably |
| A273 | yara rule name | N | high | ustart |
| A274 | attack technique name | Y | low | SQL injection (consistent with A134) |
| A275 | file path | N | high | code fragment |
| A276 | email address | N | high | phone number |
| A277 | tlp classification | Y | high | TLP:CLEAR |
| A278 | hacking tool | N | low | psql |
| A279 | file hash | N | high | literal "MD5:" label |
| A280 | threat actor group | Y | high | CL0P |
| A281 | malware family | Y | high | Snake |
| A282 | attack technique id | N | high | "Passive operations," |
| A283 | threat actor group | Y | high | Storm-0558 |
| A284 | ip address | N | low | span is IP plus URL path |
| A285 | yara rule name | Y | high | rule GRXBA declaration position |
| A286 | cve identifier | N | high | TLP marking |
| A287 | affected software product | Y | high | Jenkins (genuinely vulnerable in context) |
| A288 | yara rule name | N | high | Suricata msg |
| A289 | threat actor group | Y | high | TA505 |
| A290 | attack technique id | Y | high | T1547.006 |
| A291 | attack technique name | N | high | Snake ops mode |
| A292 | malware family | Y | high | Snake |
| A293 | file name | Y | high | Pxaz.dll |
| A294 | email address | N | high | username "admin" |
| A295 | malware family | N | high | generic word "ransomware" |
| A296 | hacking tool | N | high | code fragment |
| A297 | malware family | Y | high | Snake |
| A298 | email address | N | high | code fragment |
| A299 | file name | Y | high | LummaC2.exe; paren only |

## Totals (LLM verdicts, all 300)

- **Y: 138** (129 high-confidence, 9 low)
- **N: 162** (120 high-confidence, 42 low)
- **Low-confidence items for human adjudication: 51** (grep `| low |`)

## Systematic error classes observed (across whichever models produced them)

1. **Line-split hash fragments** judged N (A003, A012, A049, A053, A085,
   A163): the PDF layout splits SHA-256/MD5 across lines and predictions
   captured only one half. Also relevant to the pipeline itself: these
   contexts suggest `text_normalize`'s split-hash rejoin does not cover
   these table layouts.
2. **Literal "Ipv4" column tokens** predicted as ip address (A013, A027,
   A037, A078, A084, A239) — IOC-table furniture.
3. **Page furniture** ("Page", "TLP:CLEAR", "Role:", advisory IDs)
   predicted under many labels (~20 items).
4. **Code-region tokens** (Python/SQL/log fragments) predicted as
   hashes/paths/emails/tools (~35 items) — code-region detection misses.
5. **File extensions** (.vmsn/.vswp/.nvram/.vmsd) predicted as file name
   (A004, A045, A123, A231) — schema boundary question for the human pass.
6. **Dual-use tool judgment calls** (PowerShell A091, psql A142/A187/A278,
   Tor A131, Volatility A265, WinSCP A064) — the schema-intent questions
   the paper already names in RQ3.

## Data-hygiene flag for the sheet itself

A few contexts contain leaked annotation markup, e.g. A020/A027
(`` `EMAIL_...` ``/`` `IPV6_...` ``) and A270 (`` `ACTOR_...` ``). The
audit contexts appear to have been built from an annotated text variant
rather than pure `clean.md` in at least these rows — worth checking the
sheet-generation code before treating human judgments on those specific
rows as clean, and a reminder of critical invariant #1.
