# AMR to MP3 Windows Agent Notes

## Project Scope

- This repo ships a Windows desktop build of the `amr_to_mp3` app.
- Release packaging should be produced by GitHub Actions on Windows, not by local macOS builds.
- The packaging workflow is `.github/workflows/windows-package.yml`.
- The uploaded artifact name is always `AMRToMP3-windows`.

## Deployment Flow

1. Run local verification before pushing:
   - `python3 -m unittest discover -s tests -v`
2. Commit only the intended source changes.
3. Push to `main` when the goal is to produce a new Windows package.
4. The push automatically triggers `Build Windows EXE` when the change touches one of these paths:
   - `.github/workflows/windows-package.yml`
   - `amr_to_mp3/**`
   - `build/windows/**`
   - `tests/**`
   - `README.md`
   - `vendor/ffmpeg/README.md`
5. If no qualifying path changed, trigger the workflow manually with:
   - `gh workflow run windows-package.yml`

## Monitoring The Build

- List recent runs:
  - `gh run list --workflow windows-package.yml --limit 5`
- View a specific run:
  - `gh run view <run-id>`
- View logs for a specific run:
  - `gh run view <run-id> --log`

Wait for the run conclusion to become `success` before downloading artifacts.

## Downloading The Windows Package

Use these local destinations:

- Extracted folder: `artifacts/AMRToMP3-windows/`
- Zip archive: `artifacts/AMRToMP3-windows.zip`

Preferred download command:

- `mkdir -p artifacts`
- `gh run download <run-id> -n AMRToMP3-windows -D artifacts`

If replacing an older local package, remove the previous copy first:

- `rm -rf artifacts/AMRToMP3-windows`
- `rm -f artifacts/AMRToMP3-windows.zip`

If `gh run download` hits transient GitHub API EOF errors, use the artifact API as a fallback:

1. Get the artifact id:
   - `gh api repos/crynocri/amr-to-mp3-windows/actions/runs/<run-id>/artifacts --jq '.artifacts[] | select(.name=="AMRToMP3-windows") | .id'`
2. Download the zip:
   - `curl -L -H "Authorization: Bearer $(gh auth token)" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/crynocri/amr-to-mp3-windows/actions/artifacts/<artifact-id>/zip" -o artifacts/AMRToMP3-windows.zip`
3. Extract it:
   - `unzip -q -o artifacts/AMRToMP3-windows.zip -d artifacts/AMRToMP3-windows`

## Post-Download Checks

After download, verify these paths exist:

- `artifacts/AMRToMP3-windows/AMRToMP3.exe`
- `artifacts/AMRToMP3-windows/_internal/`

Useful check:

- `ls -lh artifacts/AMRToMP3-windows.zip artifacts/AMRToMP3-windows/AMRToMP3.exe`

## Git Hygiene

- Do not commit downloaded build artifacts unless the user explicitly asks for that.
- `artifacts/` is expected to remain local-only in normal packaging flows.
