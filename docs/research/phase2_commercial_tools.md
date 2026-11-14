# Phase 2: Commercial humanizer/detector surface map

**Observed:** 14 Nov 2026 (UTC+3). **Tooling:** REA `capture_browser_scenario` (Playwright driven
Chromium 157.0.8103.51, fresh temporary profile per run) and REA `inspect_api_contract`.
**Evidence bundle:** 19 REA records, exported locally (not committed: it contains third party page text).
Evidence IDs below refer to that bundle; SHA 256 digests let anyone check the public files independently.

This document records **what each tool exposes and claims**, and keeps three categories apart:

* **Observed**: seen directly in a captured request, response, page or contract.
* **Inferred**: our reading of observed facts; could be wrong.
* **Unknown**: not established.

## Scope and rules we followed

* One sample submission per site, through the site's own public UI, at normal user volume.
* No login, no paid plan, no CAPTCHA/bot challenge circumvention, no de obfuscation of payloads,
  no calls to endpoints marked internal (e.g. the `x-job-secret` usage endpoints).
* The undetectable.ai URL on the original site list carried affiliate parameters (`fpr`, `fp_sid`, `gad_source`);
  we used the bare `https://undetectable.ai/` so no referral was credited.
* Sample text (85 words, written by Claude for this test, deliberately formulaic with
  "Additionally / Furthermore / In conclusion"):

  > Regular exercise offers numerous benefits for both physical and mental health. Engaging in physical
  > activity strengthens the cardiovascular system, improves muscle tone, and enhances overall endurance.
  > Additionally, exercise has been shown to reduce stress, alleviate symptoms of anxiety and depression,
  > and promote better sleep quality. Furthermore, consistent physical activity can help maintain a
  > healthy weight and reduce the risk of chronic diseases such as diabetes and heart disease. In
  > conclusion, incorporating regular exercise into one's daily routine is essential for achieving
  > optimal health and well being.

## Summary

| Site | Mapped? | Official API | What we could observe |
|---|---|---|---|
| StealthWriter | Detector demo: yes. Humanizer: no (needs sign up) | None found | `POST /api/scan-demo`, payload obfuscated |
| HIX Bypass | **No**: page never became interactive under automation | Unknown | Claims list only |
| Undetectable.ai | Web UI: no request fired. **API: yes, from public OpenAPI** | Yes (`/develop`, OpenAPI at two hosts) | Full request/response schema |
| QuillBot AI Humanizer | **No**: Cloudflare bot challenge | None found ([one secondary source says none](https://hackceleration.com/labs/review/quillbot); UNVERIFIED with QuillBot) | Automation: nothing past the challenge. One manual run, screenshot only (see below) |

## StealthWriter (stealthwriter.ai)

**Observed** (evidence `ev_a44d14137c254008f9633ed9ddec305b7a3f42cbd261dbc2934a578a25c0e1de`):

* The homepage has a no account detector: textbox, a **V1/V2 "Scanner version"** radio (V2 default),
  "Scan for AI", 500 word cap. The humanizer link routes to `/sign-up`.
* Clicking "Scan for AI" sent `POST https://stealthwriter.ai/api/scan-demo` (fetch, 200, 320 ms).
* Request body: `{"d": "<base64>", "s": "<12 character token>"}`. Response body: the same shape.
  Decoding the outer base64 gives nonprintable bytes, so **the text and the scores are obfuscated on the
  wire**. We did not try to reverse the obfuscation. The `s` values (`mwg43bfg7cf3` → `mwg43btekhrt`)
  share a prefix, consistent with a time based nonce (inferred).
* Result shown in the UI for our sample: **"100% human, Looks Human"**, plus a per sentence
  "Deep Scan" with the legend "Green = more natural · Red = still needs work". The UI also warned:
  "Results may be inaccurate because the text is under 100 words."
* Third party scripts loaded: `cdn.affonso.io` (affiliate tracking), `googletagmanager.com`.
* Hosting: Vercel (`x-vercel-*` response headers present).

**Claims on the page** (quoted from the captured accessibility tree):

* "rewrites AI generated content so it reads naturally human"
* "Text you submit for humanization or scanning is not stored after processing is complete."
* Pricing: Free 10 humanizations/day, Starter $20/mo … Scale $400/mo for 2,000/day.

**Inferred:** On a single 85 word sample, written in a textbook AI style, the V2 scanner said "100% human".
That is one data point, and it falls below the tool's own 100 word reliability threshold, so it shows
nothing about accuracy in general. It does show that the free scanner can call stereotyped AI text human.
That is consistent with a detector tuned to make the tool's own humanizer look effective, but we have
**not** shown that.

**Unknown:** which model sits behind V1/V2; what the scores mean; anything about the humanizer.

## HIX Bypass (hixbypass.com)

**Observed:**

* `curl` received 68,913 bytes of HTML in 30 s without the response finishing. The bytes were mostly inline
  CSS for a `coco-btn` component library, served via Cloudflare (`cf-ray`).
* Three browser runs (`ev_c7288a56c91a5c0ef6cee2edd68db1f61ae2dad7a0c36a04d31bd5cb2ea7effd`, `ev_507c468136058dc0c112bd21ebef53f38ce718ebfc68cb46448a5d3dcde4f21b`, plus one that timed out before producing Evidence; headless/`load`, headless/`domcontentloaded`, headed/`commit` + wait for a text box)
  never produced an interactive text input within 40 to 90 s.
* Detector logos referenced in the HTML, i.e. the detectors the page **claims to bypass**: Originality,
  GPTZero, Turnitin, Copyleaks, Content at Scale, Crossplag, QuillBot, Sapling, Scribbr, Winston, Writer,
  ZeroGPT (`cdn.hixbypass.com/prod/public/images/bypass-ai-detection/bypass-icon/*.jpg`).

**Unknown:** everything about its API surface. The page may be throttling automated clients on purpose;
we did not test that further.

## Undetectable.ai

### Web UI

**Observed** (evidence `ev_631e1cc06e982f0286c959e90d4db708b4dbe13e6b3995ade08bc1c0a50fae2d`): the text box
(`input-detector-textarea`) accepted our text, but the word counter stayed at "0/5000". Clicking "Check for AI"
sent **no fetch/XHR request** (none appears among the 87 captured transactions). Most likely the
programmatic fill did not trigger the app's input handler (inferred). That says nothing about the product.

### Official API (public OpenAPI contracts)

Fetched 14 Nov 2026 without credentials:

| Contract | URL | SHA 256 |
|---|---|---|
| Detector | `https://ai-detect.undetectable.ai/openapi.json` (FastAPI 0.1.0, OpenAPI 3.1.0) | `c97177c57d828617712e381211a266f471b328fc28a7e34ec78c728b357ba1c8` |
| Humanizer | `https://humanize.undetectable.ai/openapi.json` (FastAPI 0.1.0, OpenAPI 3.1.0) | `1a688c22405720632d696281ac46da228821c0c679a2d6cd4f01c67dc6d43e68` |

REA operation inventories: detector `ev_417d2b4e2554ebed1ebcb94117c4192db5f1fee39dc01fcc602c8bba2ae16b61`, humanizer `ev_06ffc4fff8b65aaf2af39bc849aefb1890fcf4360377f7990dfb20f4da3b14d0` (9 operations each, complete
within scope). REA does not analyze schemas, so the field lists below were read straight from the JSON.

**Detector API (`ai-detect.undetectable.ai`)**

| Method & path | Request | Response |
|---|---|---|
| `POST /detect` | `SubmitDocumentRequest`: `key` (required), `text`, `url`, `id`, `email`, `document_type` ∈ {Document, Url, File, PDF} (default Document), **`model` (default `"xlm_ud_detector"`)**, `retry_count`, `is_streamed` (default true), `user_agent`, `generate_analysis_details`. Optional `userkey` header. | `DetectResponse` or `ErrorResponse{error}` |
| `POST /detect-pdf` | `url`, `key`, `model`, `modules[]` | same |
| `POST /query` | `{id}` | `QueryResponse` (below) |
| `GET /check-user-credits` | header `apikey` | `{baseCredits, boostCredits, credits}` |
| `GET /get-presigned-url` | `file_name`, `expiration`, header `apikey` | undeclared |
| `GET /health`, `POST /get-free-usage` | n/a | undeclared |
| `POST /organizations/{org_id}/usage[/sync-to-stripe]` | header `x-job-secret` | internal billing, not called |

**Scoring fields** (`DetectResponse` / `QueryResponse`):

* `result`: number | null, the headline score. Its scale and direction are **not documented in the contract**.
* `result_details` (`ResultDetails`, all required numbers): **`scoreGptZero`, `scoreOpenAI`, `scoreWriter`,
  `scoreCrossPlag`, `scoreCopyLeaks`, `scoreSapling`, `scoreContentAtScale`, `scoreZeroGPT`, `human`**.
* `result_categories`: `{advanced, standard, free}`, three numbers.
* `QueryResponse` adds `label`, `source_details{source, confidence, credits_deducted}`, `document_properties`.
* `status` (default `"pending"`): results are polled via `/query`.

**Inferred (important for honest comparison):** `result_details` returns one score per named third party
detector, yet the request names a single model, `xlm_ud_detector` (likely XLM RoBERTa based, going by the
name). So these per detector numbers are probably **in house predictions of what each detector would say,
not live calls to GPTZero, Copyleaks and the rest**. This is UNVERIFIED. To test it with an API key: send the
same texts to the real GPTZero/Sapling/Copyleaks APIs and compare, and check whether latency and cost scale
with the number of detectors. Either way, a `scoreGptZero` from this API must never be reported as a GPTZero
result.

**Humanizer API (`humanize.undetectable.ai`)**

| Method & path | Request |
|---|---|
| `POST /submit` | `SubmitDocumentRequest`: `readability`, `purpose`, `strength` (all **required free form strings, no enum in the contract**), `content`, `model` (default `"v2"`), `document_type` ∈ {Text, File, Url}, `url`, `id`, `user_agent`; header `apikey` |
| `POST /rehumanize` | `id`, `parent_id`, `model` (default `"v2"`) |
| `POST /document` | `{id}`: retrieve result |
| `POST /list` | query `offset` |
| `POST /handover` | `{content}` |
| `POST /token` | `{apikey}`: token exchange |
| `GET /check-user-credits` | query `wordcost`, header `apikey` |

**Observed gap:** every humanizer response schema is declared as `{}`. The contract does **not** say what
the output contains (no humanized text field, no change log, no meaning preservation score).
Allowed values for `readability`/`purpose`/`strength` are not in the contract (UNVERIFIED; check `/develop`
or test with a key).

**Claims on the site** (captured accessibility text, `ev_e63a5e7f1adc33a6e51716f56476c819adba691ac4a633448ed6099688b38ba6`):

* "Rated #1 Best AI Detector by Forbes!", not verified by us.
* The humanizer gives "Subtle rewrites that sound like you while scoring as human on every major detector."
* "Undetectable AI analyzes your text the same way a detector would … our humanizer rewrites those sections
  by varying sentence structure, enriching vocabulary, and adjusting tone."
* Product list includes an **"AI Text Watermark Remover"** and a **"Human Typer" ("human auto typer for docs")**.
  Going by the names, these target watermark based detection and document version history checks (inferred).
* "Trusted by 24M+ users", "55,012 new users this week", not verified.

## QuillBot AI Humanizer (quillbot.com/ai humanizer)

**Observed** (evidence `ev_53f7d017a0e23cd4090f22bbc2b5777e60d4cefdc77fe231d6da4aac03a59448`): after a redirect with `__cf_chl_rt_tk`, the page showed
"Performing security verification … verifies you are not a bot" (Cloudflare, Ray ID `a5a481820a5a5457`).
A plain HTTP fetch got 403. **Nothing past the challenge was observed by automation.**

### Manual run by the project owner (screenshot, 14 Nov 2026)

A project maintainer ran one humanization by hand in their own browser (free tier, mode "Concise",
English (US)) and shared a screenshot. **Source type: UI screenshot only, with no network capture**, so no
request or response fields are known. The input was the maintainer's own ~92 word professional
self description (two paragraphs). It is not reproduced here because it contains personal information.

Observed in the screenshot:

| Observation | Detail |
|---|---|
| Length | input **92 words** → output **155 words** (+68%), in "Concise" mode |
| Added content? | the output has a third paragraph (on code review practices) with no counterpart in the visible input. **Unresolved:** either the humanizer added content, or the input was edited after the run. Needs a recorded rerun |
| Broken compounds | the hyphen was removed from two compound modifiers (the input's hyphenated "Go based" and "infrastructure related" lost their hyphen), and "microservices" was split into "micro services" |
| Injected surface errors | proper noun lower cased ("Docker" → "docker"); a space inserted before a full stop ("Docker ." ) |
| Fragments | a full sentence ("At [employer], I worked on …") became a fragment ("[Employer]: Go based microservices for …") |
| Self flagged | QuillBot's own grammar underline (yellow) appears on two spans of its own output |
| Score visibility | the "% Human" figure is left blank and marked with a Premium crown on both input and output, and "0 AI signals" on both: **the free tier does not show whether the humanization changed the detection score** |
| Change highlighting | output words coloured red or blue (meaning per QuillBot's "Legend", not captured) |

**Inferred:** the broken hyphens, lower cased proper noun and stray space match the "degradation tricks"
pattern that detector evasion relies on, and that Detechum's revision mode bans
(see [architecture §6](../design/architecture.md#6-d-revision-mode)). n = 1, so this describes this run only,
not QuillBot in general.

**To get the API surface:** rerun in a tab opened by the Claude in Chrome extension (the maintainer
performs every click and any human verification step), then read that tab's network log.

## What each tool claims vs. what it does

| Tool | Claim | What we actually established |
|---|---|---|
| StealthWriter | Output "reads naturally human" | Untested (humanizer needs an account). Its own free detector called a formulaic 85 word AI paragraph "100% human" (n=1, below its 100 word threshold). |
| HIX Bypass | Bypasses 12 named detectors incl. Turnitin & GPTZero | Untested; page never loaded under automation. |
| Undetectable.ai | "scoring as human on every major detector" | The API reports per detector scores, apparently from one in house model (inferred). The contract declares no output fields for the humanizer. |
| QuillBot | humanizer output (no detection claim visible on the free tier) | Blocked by Cloudflare under automation. One manual run (screenshot): output 68% longer than input in "Concise" mode, with broken hyphens, an injected lowercase proper noun, a stray space before a full stop, and a sentence turned into a fragment; human percentage score paywalled. |

## The full black box probe (not run yet: what it needs)

The planned probe set (50 pre Nov 2022 human texts, 50 nonnative essays, 50 AI texts from known
model+prompt, plus paraphrased/edited variants) is specified in
[`../evaluation/plan.md`](../evaluation/plan.md#6-probe-set-phase-2-black-box-comparison). It was **not run**. It needs:

**Decision (14 Nov 2026): no paid subscriptions.** The project will not buy Undetectable.ai or other
vendor plans. Consequences:

1. **Undetectable.ai is not live scored.** Its API field map above came from public docs and stands. Its
   detection and humanization behaviour stays **unmeasured**, and is reported that way.
2. **Held out detectors are open models run locally**: Binoculars, Fast DetectGPT and an open trained encoder
   (e.g. GPTTrace / MELD / DeBERTa ConPara, see Phase 1). No keys or accounts are needed, and anyone can
   reproduce the scores. Free tiers of commercial detectors may be added later where their terms allow research use.
3. **StealthWriter, HIX and QuillBot are covered by small manual samples only.** The maintainer runs them by
   hand in a recorded tab, at normal user volume, within each tool's free tier. Driving their web UIs 300+
   times would be scraping, and is out of scope.
