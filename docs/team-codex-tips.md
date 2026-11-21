# Build-day tips for the team (humans, not Codex)

Goes in the repo as `docs/team-codex-tips.md`. Codex reads `AGENTS.md` by itself; this page covers what only people can do.
Sources: organiser emails (20 Nov), the official event page, OpenAI's GPT-6.2 guides and system card (read 20 Nov 2026).

## Tonight (each person, about 15 minutes)

1. **Activate your USD 100 Codex credits:** click your personal link in the organiser's email while logged in to the ChatGPT account you registered. Never share the link.
2. **Add your USD 100 API credits:** platform.openai.com → Settings → Billing → Promotions → enter your personal coupon. Never share the code.
3. **Check the Participants Package** (attached to the organiser's email): page 7 has the activation steps; it also has our table number.
4. **Get the repo:** `git clone https://github.com/Boomudm/Sea-X-OpenAI.git` into a folder of your choice. If you cannot open it, ask the repo owner to add your GitHub account.
5. **Check Codex opens and is logged in.** Send it one test question.

## Morning (critical)

- **Arrive by 08:30. Check-in closes strictly at 09:00; if any one of us is missing, the whole team is disqualified.**
- Bring: your **original** ID card or passport (for the building pass), the Lu.ma QR ticket on your phone (Lu.ma → Your Events → the event → My Ticket), laptop and charger.
- Place: Shopee Office, Singha Complex, **25th floor**. Get the access card on the G floor first.
- 09:00–10:00: find our table; ask the crew how to hand in and how long the demo is; write the answer in `README.md`.
- **10:00:** 5-minute decision check (`AGENTS.md` §0.2), then build. Milestones: capture 11:30 · end-to-end 14:30 · evaluation 15:30 · rehearsal 16:00 · **code freeze 17:00**.
- **Check out** at the desk before you leave, or no e-certificate.

## The API key (one person, once)

1. Create a key at platform.openai.com → API keys.
2. In the project folder, create a file named `.env` containing one line: `OPENAI_API_KEY=` followed by the key.
3. Make sure `.gitignore` contains `.env` **before the first commit**. Never paste the key into a prompt, a screenshot or the chat.

## Pick the model and effort

| Job | Model | Effort |
|---|---|---|
| Normal coding, small features, fixes | **GPT-6.2 Sol** (about a quarter of Astra's price per token, and close to Astra on code) | Medium |
| Tracing one specific bug across files | Sol, or Astra if Sol is stuck | High |
| A messy bug where several causes may interact | **GPT-6.2 Astra** | Extra High |
| Big work that splits into independent parts | Astra | Ultra, if your menu shows it (Codex then adds helpers itself) |

## Write each task in two short paragraphs

1. **What to do, and how we will check it.** "Add X. Done means: Y works when I run Z, and the tests pass."
2. **What Codex may decide alone, and when to come back.** "Choose details yourself if they are easy to undo. Ask me before changing the data shapes in AGENTS.md."

Codex already follows the working agreement in `AGENTS.md` (it reports what it could not check), but if an answer looks too confident, ask: **"List anything you could not run or check."**

- Write prompts in English. A Thai AI practitioner found that Thai prompts looped more; translate first if needed.
- For bigger jobs, say: **"Plan first and wait for my OK before changing files."** Read the plan, then say go.
- For independent parts: "Use subagents as needed, then compare the results."
- Two people should not ask Codex to edit the same file at the same time.
- Codex adds a row to `docs/codex-log/<your git user.name>.md` for every task that changes code, tests, data or prompts (judges score "effective use of Codex"). Check that it did; if not, ask: "Add the Codex log row for this task." Set your name once: `git config user.name "<name>"`.

## Git in five words (Codex runs the commands)

| Word | Meaning |
|---|---|
| clone | download the repo |
| branch | your own copy to work on |
| commit | a save point |
| push | upload your save points |
| PR | ask the team to merge your branch |

Say: "Create a branch called `<name>`, commit, push, and open a PR to the repo's default branch." (Today the default branch is `prep/research`; the team may rename it.)

## Never

- Never share the organiser's personal activation links or coupon codes.
- Never commit `.env` or paste an API key anywhere.
- Never write "fake" or "fraud" in what the product shows.
