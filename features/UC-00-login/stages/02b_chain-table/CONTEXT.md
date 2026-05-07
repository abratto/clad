# Stage 02b — Chain table (UC-00-login)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | UC-00-login scenarios |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | Available concepts and actions |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Forward link to Stage 03 |
| `../../../../templates/chain-table.md` | 3 | Output template |

## Process

For each named scenario in `01_usecase/output/usecase.md`, produce
`output/<scenario-name>-chain.md` using only concepts and actions
from `02a_responsibility-map/output/responsibility-map.md`. The
chain is the ordered list of concept actions that fulfils the
scenario; the last row is `Web.respond`.

## Outputs

- `output/successful-login-chain.md`
- `output/wrong-password-chain.md`
- `output/unknown-user-chain.md`
- `output/lockout-chain.md`

## Verify

- Every scenario has exactly one chain file.
- The first row is `Web.handle`; the last row is `Web.respond`.
- Every action used appears in the responsibility map.

## Gate

Default human approval. **Do you agree with this step? Any
corrections before I continue?**
