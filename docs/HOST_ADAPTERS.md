# Host Adapters

UnderOne skills can be installed into multiple agent products from the same source tree.

## Built-in Profiles

| Host | Aliases | Layout | Default Root | Notes |
|---|---|---|---|---|
| `codex` | - | `frontmatter-wrapper` | `~/.codex/skills` | Adds `agents/openai.yaml` for Codex discovery. |
| `workbuddy` | `work-buddy`, `wb` | `frontmatter-wrapper` | `~/.workbuddy/skills` | Uses the same wrapper style without extra Codex files. |
| `qclaw` | `openclaw`, `claw` | `native-source` | `~/.qclaw/skills` | Best fit for OpenClaw-like products that read native `SKILL.md` layout. |
| `custom` | `third-party`, `thirdparty` | `native-source` | requires `--dest` | Generic path for third-party products and local experiments. |

## Install Rules

- Use `codex`, `workbuddy`, or `qclaw` when the target product matches a built-in profile.
- Use `openclaw` or `claw` as readable aliases for `qclaw`.
- Use `custom` for third-party products and always pass `--dest /path/to/product/skills`.
- Keep each skill installable and testable on its own; never require the full ecosystem for a single skill to work.
- Validate the installed copy with `skillctl.py self-test` after installing into any host.

## Commands

Run these commands from the repository root.

```bash
# Built-in host roots
python underone/scripts/install_host_skills.py --host codex
python underone/scripts/install_host_skills.py --host workbuddy
python underone/scripts/install_host_skills.py --host qclaw

# OpenClaw-like product with an explicit product directory
python underone/scripts/install_host_skills.py --host openclaw --dest /path/to/openclaw/skills

# Generic third-party product
python underone/scripts/install_host_skills.py --host custom --dest /path/to/product/skills

# One skill only, useful for validation and optimization loops
python underone/scripts/install_host_skills.py --host custom --dest /tmp/underone-custom fenghou-qimen
python /tmp/underone-custom/fenghou-qimen/skillctl.py self-test
```

## Adapter Policy

Add a dedicated built-in profile only when a product needs a stable wrapper format, extra files, or a known default directory. Use `custom` for products that can consume the native source layout directly.
