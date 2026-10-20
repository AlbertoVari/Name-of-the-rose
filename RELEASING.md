# Publish v0.1.0

The source package is ready for a GitHub repository named `name-of-the-rose`.
The repository is https://github.com/AlbertoVari/Name-of-the-rose.
The CI workflow has a release job that runs only after successful validation on
a push to main. It creates v0.1.0 at the validated commit using GitHub Actions'
short-lived repository token with contents-write permission scoped to that job.
Pull requests cannot run the release job. An existing release is left unchanged.
Confirm the hosted run and release URL before claiming publication.
The commands below remain an alternative for an authorized local maintainer.

## From an extracted source archive

Run the README checks first. Install/authenticate the official GitHub CLI in
your own development environment if needed. From the extracted project root:

```sh
git init -b main
git add .
git commit -m "Release The Name of the Rose v0.1.0 POC"
git tag -a v0.1.0 -m "First evidence-linked COBOL semantic POC"
gh repo create AlbertoVari/Name-of-the-rose --public --source=. --remote=origin --push
git push origin v0.1.0
gh release create v0.1.0 --repo AlbertoVari/Name-of-the-rose --verify-tag --title "The Name of the Rose v0.1.0" --notes-file CHANGELOG.md
```

These commands create a public repository. Change the owner/name or visibility
deliberately if required. If the repository already exists, inspect it before
adding a remote or pushing; do not overwrite unrelated work. Do not force-push.
The `.upstream` directory and caches are ignored and must remain absent from the
commit. The versioned `build/` directory is intentionally included.

## Connector-assisted continuation

Create a repository with an initial README commit, grant the existing GitHub
connection access to it, and provide its URL. An initial commit is needed for the
connector's commit API. The prepared tree can then be committed after checking
the existing contents. The connector exposed in the build session has no release
creation endpoint; creating the final tag/release requires an available GitHub UI
or CLI. Never describe a committed tree as a published GitHub release.

## Final gate

1. Confirm all required files, source hashes and reviewed mappings.
2. Run `make check SOURCE=.upstream` and record the actual result.
3. Run the Copilot smoke test in `docs/copilot.md`; record host/version and actual
   delegation or manual handoffs. If deferred, keep that limitation visible.
4. Review `docs/acceptance.md`, license boundaries and known gaps.
5. Publish the tag/release; verify repository URL, tag commit, release URL and
   hosted Actions result. Record publication evidence separately from local tests.
