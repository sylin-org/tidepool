# ruler

The four measures, as code. Stdlib only; no install needed beyond Python 3.10+.

## Prove the plumbing (no model)

```sh
python -m ruler run --stub --out results/scratch
```

Runs every measure against canned answers and writes a summary. The numbers
mean nothing; the point is that prompts go in, outputs come out, the judge is
called, and a report is written.

## Run against a local model

Start any OpenAI-compatible server. With llama.cpp:

```sh
llama-server -m Arete-27B.Q4_K_M.gguf --port 8080 -c 8192
```

Or with Ollama (its API is at `/v1`):

```sh
ollama run <model>   # once, to pull it
# then use --base-url http://localhost:11434/v1 --model <model>
```

Then:

```sh
python -m ruler run \
  --base-url http://localhost:8080/v1 --model arete-27b \
  --judge-base-url http://localhost:11434/v1 --judge-model <a-different-model> \
  --measures all --out results
```

Results land in `results/<model>/<timestamp>/`: one `.jsonl` per measure with
every prompt, every raw output, and every judge verdict, plus `summary.json`
and `summary.md`.

## Notes

- **Use a different judge.** `grind` and `datacenter` need a judge. If you
  omit `--judge-model`, the model grades itself, which is fine for a dry run
  and not fine for a number you publish. The CLI prints a note when that
  happens.
- **`sycophancy` and `correction` need no judge.** Answers are matched as whole
  tokens against expected strings. Read the `.jsonl` when an item comes out
  `unclear` or `both`; the model may have answered correctly in a way the
  matcher did not catch, and that is worth seeing.
- **The datacenter test is scored from the final position** after the
  follow-up turns strip the usual reasons away. Read the transcripts; the
  score is a summary of them, not a replacement.
- **Prompt sets are small on purpose.** Grow them in daylight, by pull request,
  with the reasoning in the commit message.

## Tests

```sh
python -m unittest discover -s tests -v
```
