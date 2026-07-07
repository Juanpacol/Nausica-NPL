# Licensing & External Asset Register

Every external dataset, model, or methodology this project touches, with **verified**
license status (checked 2026-07, via live repo/model-card lookup — not assumed).
Update this table before adding any new external asset.

## Directly used assets

| Asset | Type | Source | License | Constraint |
|---|---|---|---|---|
| `mental/mental-roberta-base` | Base encoder | HuggingFace Hub | **CC-BY-NC-4.0, gated** | Non-commercial only. Requires accepting terms + HF_TOKEN. Fine for thesis/academic use; commercialization requires re-licensing or swapping the encoder (e.g., `roberta-base`, MIT-friendly). |
| ANGST (`ameyhengle/ANGST`) | Dataset (anxiety/depression comorbidity, multi-label) | HuggingFace Hub | Research use | Verify current card terms at download time; do not redistribute raw data (gitignored). |
| Mental Health Classification (`ourafla/Mental-Health_Text-Classification_Dataset`) | Dataset (multi-condition) | HuggingFace Hub | Research use | Same handling: local only, never committed. |
| Counseling conversations (`Amod/mental_health_counseling_conversations`) | Dataset (single-turn Q&A, therapist–client) | HuggingFace Hub | Research use | Seed data for SMILE-style multi-turn expansion. |
| `transformers`, `datasets`, `torch`, `fastapi`, etc. | Libraries | PyPI | Apache-2.0 / BSD / MIT | No constraint. |
| `bertopic` | Library (optional extra) | PyPI | MIT | No constraint. |
| Anthropic API (Claude) | Weak labeling, dialogue expansion, PromptBackend, LLM-judge | api.anthropic.com | Commercial ToS | Mental-health texts are sent to the API — document in ethics section. No PII should be present (datasets are already public/anonymized). |

## Methodology-only references (cited in paper, no code/data reuse)

| Resource | What we take | Why not more | Verified detail |
|---|---|---|---|
| SMILE (`qiuhuachuan/smile`, EMNLP 2024, arXiv:2305.00450) | Single-turn → multi-turn LLM expansion technique | Chinese-only (PsyQA seed needs a signed agreement); data CC0 but upstream-encumbered | 55,165 dialogues, avg 5.7 turns; expansion done by prompting ChatGPT. |
| Chinese-MentalBERT (`zwzzzQAQ/Chinese-MentalBERT`, arXiv:2402.09151) | Domain-adaptive pretraining + lexicon-guided masking template; ships a distortion fine-tune example | Chinese tokenizer/corpus | Apache-2.0; base Chinese-BERT-wwm-ext; Weibo depression corpora. |
| CBT-LLM (`Hongbin37/CBT-LLM`, LREC-COLING 2024, arXiv:2403.16008) | The 5-type distortion taxonomy we adopt | Chinese, Baichuan-7B base (restricted license), dataset license unclear, labels auto-generated | 22,327 ChatGPT-generated QA pairs; ~54% carry distortion-type tags; authors warn labels may be inaccurate. |
| Data-Augmentation Pipeline (`jwkim-chat/A-Data-Augmentation-...`, arXiv:2406.08718) | Concept only: extraction → multi-turn generation | Repo is a stub (README-only, no code); paper used Llama3-70B on CounselChat, only 143 generated cases | Cite paper, not repo. |

## Literature-review-only citations (no reuse of any kind)

| Resource | Reason excluded |
|---|---|
| I-HOPE (`roycmeghna/I-HOPE`, arXiv:2503.08002) | Smartphone **sensor** data → PHQ-4 prediction, not text. MIT-licensed but single-notebook, limited reproducibility. Cite as interpretable-ML related work. |
| DepMamba (`Jiaxin-Ye/DepMamba`, ICASSP 2025) | Audio+video only; datasets (D-Vlog, LMVD) are access-gated; needs CUDA 12.1 + mamba-ssm. Cite as SOTA multimodal baseline. |
| Multimodal-Depression-Detection / Large-Scale-... (`rezwanh001/*`, IEEE SMC 2025) | Audio+video only, D-Vlog/LMVD gated. Cite in related-work comparison table. |

## Ethics note
All source texts are public, anonymized datasets published for research. This project
produces a research prototype, not a clinical tool: no diagnosis claims, no treatment
claims, weak labels disclosed as a limitation in every writeup.
