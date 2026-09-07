# Independent preimplementation review

Reviewer: independent GPT-6 Astra, low reasoning effort, read-only.
Scope: roadmap, implementation contract, readiness record, evidence manifest,
preserved second Pro review/script, and decisions to retain the offline oracle,
historical work, test infrastructure, and current gameplay policy.

**APPROVE — ready for the restricted offline prototype.** No required changes
remain in the preparation package. This approval includes every stated retention
decision: frozen offline oracle/current helpers, existing tests/reference
evaluators, historical analyses/strategic stages, and unchanged gameplay policy.

The reviewer checked all 30 manifest artifact hashes. Reviewed manifest SHA256:

    BB8168A6C34EA5701E0F05D16B3E6F54CB68AC3CB88A1CC0BE11FB40DE98D51F

Reviewed substantive document SHA256 values:

| Document | SHA256 |
| --- | --- |
| two_second_roadmap.md | 9006394EAF4BC1A957AB3BD0A4837757AD8B571EBDE434986B312D087416AA7C |
| selector_implementation_contract.md | 147DF5687334A407234D6E9EEE36630839CC6DA6412051F0D709FA49A52A38CE |
| selector_readiness.md | 7E7559E74DA08326701D687DC3B26F15EF4EDE7E3CC026D97769019DA54D27DF |

Initial source findings incorporated into the contract:

- FarCall clobbers A; use the exported result and a later explicit public wrapper.
- SRAM helpers provide no tracked previous-bank restoration; require closed
  entry, bank 0 ownership, closed exit.
- Animation scratch aliases live battle-animation objects; VBlank can execute
  graphics handlers and change RNG. Prototype harness masking does not prove
  interrupt-enabled gameplay ownership or latency.
- Direct fallback masks prepared bits and uses the first 89 bytes; legacy HP
  tables cannot coexist with the proposed SRAM records.
- Rank8 has explicit maxHP/weight/size eligibility; wider input is not free.
- Identity certification covers every continuation, not standalone utility.

Focused source review found no blocker to retaining the tested current helper
state as an offline oracle: normalized actor/stat preparation, 16-entry accuracy
cache with exact fallback/reset, and four-byte attribute loading/remapping.
Prepared/direct comparisons share the bulk loader, so its source mapping and
combat/descriptor regressions are part of the evidence rather than counting
those comparisons as independent proof of the loader.

This review does not approve native performance, new implementation, or production
integration. Complex finishing/multihit count bounds also remain unverified.
