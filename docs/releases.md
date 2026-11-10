# Releasing content

Keep distributable DAT and generated IDX files out of Git. Put the catalog, metadata, licenses, dated notices and corresponding source in the release commit. Attach the exact DAT files and the companion notices and checksums to a GitHub Release for that commit's tag.

Catalog URLs follow this pattern:

```
https://github.com/StudioNulem/nCave-content/releases/download/<tag>/<file>
```

Publish a new tag for changed bytes. Do not overwrite a file under an existing tag: clients may pin the URL and SHA-256 for that version. Keep each release's licenses and corresponding source available at its tag.

Before publishing, verify the staged assets from the repository root:

```sh
python3 docs/verify_release.py /path/to/content-2026.11.1
```

After publishing, download all four assets anonymously using the URLs in the catalog, then repeat the verification on the downloaded files. Do this before enabling those URLs in a downstream app release.
