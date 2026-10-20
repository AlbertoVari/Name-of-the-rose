# Publish v0.1.0

The source package is ready for a GitHub repository named `name-of-the-rose`.
The repository is https://github.com/AlbertoVari/Name-of-the-rose.
The CI workflow has a release job that runs only after successful validation on
a push to main. It creates v0.1.0 at the validated commit using GitHub Actions'
short-lived repository token with contents-write permission scoped to that job.
Pull requests cannot run the release job. An existing release is left unchanged.
Confirm the hosted run and release URL before claiming publication.
The commands below remain an alternative for an authorized local maintainer.

## Published release and future versions

v0.1.0 is published at https://github.com/AlbertoVari/Name-of-the-rose/releases/tag/v0.1.0.
Its tag points to `5c49334872b4cd99d3a3df3b38b18888fe3cd4d6`; subsequent
publication-status documentation commits do not move that immutable release tag.

For a future release, review the version, changelog and workflow tag together.
The current workflow intentionally leaves v0.1.0 unchanged on later pushes.
Use a fresh version tag; never overwrite a published release to hide corrections.
An authorized maintainer can publish manually after checks using the official
GitHub CLI and `gh release create`, with an explicit validated target commit and
release notes file. Do not recreate the existing repository.

The `.upstream` directory and caches remain excluded. The versioned `build/`
directory is intentionally included. No upstream COBOL source is redistributed.

## Final gate

1. Confirm all required files, source hashes and reviewed mappings.
2. Run `make check SOURCE=.upstream` and record the actual result.
3. Run the Copilot smoke test in `docs/copilot.md`; record host/version and actual
   delegation or manual handoffs. If deferred, keep that limitation visible.
4. Review `docs/acceptance.md`, license boundaries and known gaps.
5. Publish the tag/release; verify repository URL, tag commit, release URL and
   hosted Actions result. Record publication evidence separately from local tests.
