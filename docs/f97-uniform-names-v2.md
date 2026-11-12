# Original UniformSetter name contract, version2

The material checks now have a versioned successor for native uniform names. `_uniform_loader.py` remains the unchanged historical v1 module. `_uniform_loader_v2.py` corrects the declared caller string-pool base to serialized pool start plus8. The original reference-minus6 arithmetic consequently produces the real NUL-terminated character pointer. V2 reads that pointer directly and calls the original lookup routine with a separately copied query string, exercising the actual comparison rather than relying on pointer identity.

V1's66 single-entry numeric experiments still executed the original constructor/reader and copied the expected0,0.375 and1 values. Their numeric bytes remain unchanged. However, v1 inspected `nativeName+8` and called it the native name: that interpretation was incorrect. It did not prove subsequent native C-string lookup or multiple distinct uniform names. The old module and historical hashes must not be relabelled as corrected name proof.

The genuine ECO record contains four scalar entries including `u_SLDActive=0` and `u_SLDLimit=1`. V2 runs it with both zero/A5 allocation fills and both caller origins, yielding4 regression executions. With the correct origin, the original reader preserves all4 entries and the original lookup distinguishes both names and values. With the raw v1 origin, the native list merges to3 entries and real C-string queries find neither name; these are explicitly rejected caller-input witnesses, not accepted results or a firmware defect. Source instructions and source scalar values are unchanged. No fabricated hash initializer, kernel reply or field patch is used.

The v2 original material report retains66 uniform numeric cases,48 asset-identifier cases and96 image-cache-boundary cases, and adds4 uniform-name regression cases:214 total. Complete provider/scene/kernel/GPU startup and vehicle compatibility remain unproved.

Firmware-free admission tests run normally. To run the original-code regression tests locally, install the optional research dependencies and set `KOMBIKRAFT_F97_BANK`, `KOMBIKRAFT_F97_SCENE` and `KOMBIKRAFT_F97_NOR` to your matching locally supplied files, then run:

```sh
python -m unittest discover -s tests -p test_research_f97_uniform_v2.py
```

Exact source-profile hashes are enforced. The repository contains authored harness source, resource names and interpretation metadata, without the firmware code banks or machine-specific paths used for research.
