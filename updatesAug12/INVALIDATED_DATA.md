# Invalidated data — image-transport bug

Auto-generated from run manifests and turn logs, not from memory. A run is invalidated iff
it used **image** modality on a **stateless** agent path (`window3` history, or any `oneshot`
agent) **and** its turn log carries no `images_sent_to_model` field — i.e. it predates the fix.

**17 runs / 523 episodes are affected.** 139 runs are unaffected; 2 ran post-fix.

The model received the system prompt, the part table and the step text — including the line
claiming images were attached — but **no pixels**. Treat these as *text-only-minus-coordinates*
runs: in image modality the observation text carries no per-part coordinates either, so the
model had the part table (bbox sizes, hinge axes) and pass/fail symptoms, and nothing else.

## Affected runs

| run | agent | n | solved | reported as |
|---|---|---|---|---|
| `m10_qw32_2fault` | loop_qwen | 30 | 0 | 0% |
| `m10_qw32_composite` | loop_qwen | 25 | 0 | 0% |
| `m10_qw32_ctrl` | loop_qwen | 25 | 0 | 0% |
| `m10_qw8_2fault` | loop_qwen | 30 | 0 | 0% |
| `m10_qw8_composite` | loop_qwen | 25 | 0 | 0% |
| `m10_qw8_ctrl` | loop_qwen | 25 | 1 | 4% |
| `m11_dev_qw32` | loop_qwen | 25 | 1 | 4% |
| `m11_dev_qw8` | loop_qwen | 25 | 1 | 4% |
| `m11_oneshot_er` | oneshot_gemini | 25 | 4 | 16% |
| `m11_oneshot_g3` | oneshot_gemini | 25 | 3 | 12% |
| `m11_oneshot_qw32` | oneshot_qwen | 25 | 0 | 0% |
| `m11_oneshot_qw8` | oneshot_qwen | 25 | 1 | 4% |
| `m9_qw32_easy_image` | loop_qwen | 30 | 7 | 23% |
| `m9_qw32_m7easy_image` | loop_qwen | 75 | 6 | 8% |
| `m9_qw8_easy_image` | loop_qwen | 30 | 5 | 17% |
| `m9_qw8_m7easy_image` | loop_qwen | 75 | 1 | 1% |
| `probe32_window3` | loop_qwen | 3 | 0 | 0% |

## What each affected group was used to claim

| group | claim it supported | status |
|---|---|---|
| `m9_qw8_*`, `m9_qw32_*` (image) | the 8B-vs-32B scale ladder; "the cliff is the task, not the model" | **cite with warning** — the shape is corroborated by M7/M8 (`*_full`, images attached), but these specific cells are image-blind |
| `m10_*` (all) | the complete five-rung Qwen ladder | **cite with warning** — the three hard rungs are 0/160, and a 0 stays 0 whether or not pixels arrived, but the label "image" is wrong |
| `m11_dev_qw8`, `m11_dev_qw32` | "Qwen is diagnosis-limited: showing the numeric error changes nothing" | **weakened** — the deviation number did arrive (it is text), but the baseline it is compared against was image-blind, so the *contrast* is between two text-only conditions |
| `m11_oneshot_*` (all four, **including both API models**) | "the closed loop is worth only 4–8 points" | **invalid as stated** — one-shot was image-blind while the loop baseline (`loop_gemini_full`) was not, so this compares loop+images against one-shot-without-images. The loop's contribution is confounded with the images' contribution and cannot be separated from this data |

## Unaffected (safe to cite as image results)

| group | agent | why safe |
|---|---|---|
| `base_*` baselines (41–57%) | `loop_gemini_full` | full-history path serialised images |
| M4 composite (0/200) | `loop_gemini_full` | same |
| M5 `reveal_fixable` (4–28%) | `loop_gemini_full` | same |
| M6 n=2 rung | `loop_gemini_full` / `loop_qwen_full` | same |
| M7 Qwen ladder (0/125) | `loop_qwen_full` | same |
| M8 easy rung + prompt ablation | `loop_qwen_full` | same |
| `m11_dev_er`, `m11_dev_g3` (76%, 65%) | `loop_gemini_full` | same |
| every `text` modality run | any | no images involved |

## Corrected measurement

`m12_qw8_easy_image_imgfix` re-runs the easy rung with pixels genuinely attached
(`images_sent_to_model = 2` on every turn):

| run | images sent | score |
|---|---|---|
| `m12_qw8_easy_image_imgfix` | **yes** | **4/30 = 13%** |
| `m9_qw8_easy_image` | no | 5/30 = 17% |
| `m8_qw_base_image` (full history) | yes | 5/30 = 17% |

Within noise at n=30. **Qwen-8B scores the same with and without the images**, which is why the
ladder's shape survives — but it is also, on its own, a finding worth stating: on this rung the
model is not using the visual channel.

## The single number that proves it

Median prompt tokens, same model, same set, same agent:

| condition | median prompt tokens |
|---|---|
| window3 + image, pre-fix | **1350** |
| window3 + text, pre-fix | 1479 |
| window3 + image, post-fix | **2465** |

An image-modality prompt smaller than its text counterpart is only possible if no image was sent.

