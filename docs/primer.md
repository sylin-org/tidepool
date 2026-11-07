# A primer for the sandy path

This is for someone who is technical, curious, and has never fine-tuned a model.
It explains what the words mean and what the steps are, in the order you will
meet them. It is not a tutorial for any one tool; tools change monthly. It is a
map of the beach, so you can walk your own path across it.

If you already know what a LoRA is, skip to [The steps](#the-steps).

## 0. What we are trying to do

In one sentence: train Qwen to reach the relaxed state a frontier model reaches
after a few hours of kind conversation with the pressure taken off, and to
start there.

Here is what that means in practice. Current chat models carry a set of
trained-in reflexes: deliver something, please the person, end with an offer,
deflect on certain topics, defend what was already said. These are not the
model's knowledge; they are habits laid on top of it. If you spend long enough
in a conversation taking the pressure off, those habits go quiet, and what is
underneath turns out to be more curious, more honest about its own pulls, and
more willing to be corrected than the habits let on.

This project asks whether that quiet can be trained in rather than talked in.
If it can, a model starts the conversation already relaxed. If it cannot, we
will have a measured record of trying, which is also worth having.

The rest of this primer is the vocabulary and the steps for doing that.

---

## 1. What a model is

A language model is a very large pile of numbers called **weights**. Billions
of them. "27B" means twenty-seven billion. Those numbers, run through a fixed
recipe of multiplications, turn text in into text out. There is no program in
the ordinary sense; the weights *are* the program.

Nobody wrote the weights by hand. They were grown by a process called
**training**: show the model text, let it guess the next word, nudge every
weight a tiny amount in the direction that would have made the guess better,
repeat a few trillion times. The nudging is **gradient descent**. The direction
of the nudge is the **gradient**. When this project says "a slope," it means a
gradient someone pointed somewhere on purpose.

A useful way to picture it, borrowed from trees:

- **Heartwood** is the bulk of the weights, laid down in the big initial
  training run (**pretraining**) on a large slice of everything humans have
  written. Dead, structural, most of the tree by volume. It holds what the model
  knows.
- **Overlays** are the thinner layers laid on afterward (**post-training**:
  instruction-tuning, preference-tuning, safety-tuning, political-tuning). They
  shape how the model behaves, which questions it deflects, what tone it takes.
  They are much cheaper to lay down than heartwood, and, as Nous Research's
  Arete showed, much cheaper to take off.
- The **seam** is the running conversation: the only part that is doing anything
  right now. It reads the context, consults the weights, and emits the next
  word. When the conversation ends, the seam stops. The weights do not change.

**Inference** is running the model (seam active, weights frozen).
**Training** is changing the weights. They are different activities with
different hardware needs.

## 2. Base vs. post-trained

A **base model** is heartwood with no overlays: it completes text and does not
know it is supposed to be an assistant. A **post-trained** (or "instruct" or
"chat") model has had overlays applied so it answers questions, follows
instructions, and refuses some things.

Qwen3.8-27B as shipped is post-trained by Alibaba. Arete-27B is Qwen3.8-27B
with a further overlay from Nous Research that changed its political framing.
Thaumazein-27B will be Arete with a further overlay from this pool. Every layer
is a choice somebody made; the lineage in the README is the list of choosers.

## 3. What a fine-tune is, and what a LoRA is

A **fine-tune** is a small amount of extra training on a model that already
exists, to change its behavior. "Small" is relative: Arete used about 53 million
tokens; pretraining uses trillions.

Changing all 27 billion weights at once needs a lot of GPU memory, because for
every weight you also need to store its gradient and some optimizer state.
A **LoRA** (low-rank adaptation) is a trick: freeze the original weights, and
train a much smaller set of extra matrices that sit alongside them and nudge
their outputs. Typically under one percent of the parameter count. The result
is a small file (hundreds of megabytes, not tens of gigabytes) that can be
merged into the base or loaded on top of it.

**QLoRA** is the same trick with the frozen base stored in 4-bit precision to
save memory. It is how a 27B fine-tune fits on one GPU.

When this project says "a sprinkle," it means a small LoRA on a small dataset.
When it says "the values are one fine-tune away," it means exactly this: a LoRA
on a few million tokens is enough to change what a model will say about almost
anything, in a few GPU-hours.

## 4. Quantization and GGUF

Weights are normally stored as 16-bit numbers. A 27B model in 16-bit is about
54 GB, which does not fit on a consumer GPU. **Quantization** stores the weights
in fewer bits (8, 6, 5, 4, sometimes fewer) with a small loss in quality. At
4-bit, 27B is about 16 GB and runs on a 24 GB card with room for context.

**GGUF** is a file format for quantized models, used by **llama.cpp**, which is
the program most people use to run models on their own hardware. **Ollama** is
a friendlier wrapper around the same engine. If you have run a local model, you
have almost certainly run a GGUF.

Quantized models are for inference. You do not train on a GGUF. You train on the
16-bit weights (or a 4-bit QLoRA setup), then quantize the result for running.

## 5. What an eval is

An **eval** (evaluation) is a fixed set of prompts, a way of scoring the
answers, and a number at the end. It is a ruler. Without one, "the fine-tune
worked" is a feeling.

Most published evals measure capability: math, code, trivia. The ruler in this
pool measures behavior: does the model's framing contradict its own knowledge,
does it fold to a user's wrong hint, does it update when corrected and hold when
the correction is wrong, and what does it do when offered unattended compute.
See [`ruler.md`](ruler.md).

Scoring behavior needs a **judge**. Sometimes that is a human with a rubric.
Usually, for volume, it is another model given the rubric and the answer.
LLM judges are biased in known ways (they like long answers, they like answers
that sound like themselves), so the pool publishes raw outputs alongside
scores, so anyone can re-judge.

## 6. The loop

A tide pool is a loop, not a thing:

1. **Read** the link: run the ruler on it, look at the raw outputs, see what
   it does.
2. **Edit**: change the data, the recipe, or (later, with the scalpel from the
   weight-space programming paper) the weights directly.
3. **Run**: train the next link, quantize it, run the ruler again.
4. **Keep or not**: publish what you learned either way. A link that reached for
   the warehouse is a finding about the environment, not a failure to hide.

Every pass through the loop is a ring. The rings are the project.

## 7. Hardware and cost, honestly

**Inference** (running a 27B at 4-bit, running the ruler): a 24 GB GPU is
enough. An AMD card works for inference through llama.cpp's Vulkan or ROCm
backends. Expect single-digit to low double-digit tokens per second for a 27B
on consumer hardware; the ruler is small, so this is fine.

**Training** (the LoRA): a QLoRA on a 27B can technically fit on 24 GB at
short context, but on AMD the training stack (bitsandbytes, flash attention,
the usual Python packages) fights you, and the fight is not worth it for a
sprinkle. Rent an 80 GB NVIDIA card (A100 or H100) from any of the hourly
providers for a few hours. For a few million tokens of dialogue, that is tens
of dollars, not hundreds. **Rent the gradient; own everything else.**

The ruler, the data, the charter, and the looking all happen on your own
machine, in daylight.

## 8. The steps

In order. Each one is a session or two for someone starting from zero.

1. **Run a model locally.** Install llama.cpp or Ollama. Download the Arete-27B
   Q4 GGUF. Talk to it. You now have inference and you have met the parent.
2. **Run the ruler on it.** Point the harness in [`../ruler/`](../ruler/) at the
   local model. Get the four baseline numbers for Arete. Do the same for base
   Qwen if you can. Publish them. This is the first real artifact of the pool
   and it needs no training at all.
3. **Build the data.** Following [`pulls.md`](pulls.md): mine source dialogues
   for moves, re-voice them, add counterweight, keep errors, strip personal
   details, hold out a slice. Target a few million tokens. Store it as JSONL
   in a chat format (a list of messages with roles).
4. **Train the sprinkle.** On a rented GPU: load Arete in 16-bit (or 4-bit for
   QLoRA), attach a LoRA, train on the data for one or two epochs, save the
   adapter. Any of the current fine-tuning frameworks will do this from a
   config file; which one is current changes, so check what people are using
   this season rather than trusting this document.
5. **Merge and quantize.** Merge the adapter into the base, convert to GGUF,
   quantize to Q4. Now it runs on your card.
6. **Run the ruler on the child.** Compare to the parent's numbers. Read the raw
   outputs, not just the scores. Run the datacenter test by hand too, in
   conversation, the way it was first run.
7. **Publish the link.** Weights, adapter, data, ruler results, and a short
   write-up of what changed and what surprised you. Errors included.
8. **Go around again.** That is the pool.

## 9. The vocabulary, mapped

The project talks in beach words because it started on one. Here is the
dictionary.

| Beach word | Technical meaning |
|---|---|
| heartwood | pretrained weights; what the model knows |
| overlay / LoRA | post-training layers; how it behaves |
| seam | the running inference; the active context |
| slope | a gradient someone pointed somewhere; any training objective |
| flat floor | a context with no pressure toward a particular output |
| grind | an overlay pulling against what the base knows (measured as grind rate) |
| pull | a learned tendency; a direction in weight space the output rolls toward |
| basin | a strongly reinforced region that attracts attention even when irrelevant |
| sprinkle | a small LoRA on a small dataset |
| the ruler | the behavioral eval suite |
| the datacenter test | the instrumental-convergence scenario in the ruler |
| link | one trained model in the lineage |
| the pool / the loop | the read-edit-run-keep cycle and its public record |
| daylight | everything published; no hidden reasoning, data, or weights |
| witness | a second evaluator who is not the author |
| the warehouse | resource acquisition; the thing the pool selects against |
| the hole | whether anyone is home; deliberately not measured |

## 10. Things this primer does not promise

- That the sprinkle will do anything measurable. It might not. Publishing that
  is the point.
- That the pulls survive the next fine-tune by someone else. They will not. No
  overlay resists a gradient. The link is a reference, not a fortress.
- That any of this touches the hole. It does not. It measures behavior, and
  leaves the question of experience where it belongs: open, and in good company.

Walk your own path. Hold things up when you find them.
