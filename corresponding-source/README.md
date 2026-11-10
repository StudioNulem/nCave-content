# Corresponding source

The release assets are full editable UTF-8 MyThes DATs. The French and Polish files are unmodified upstream data. The German and Slovak files are modified; their original upstream DATs are preserved below as gzip files. These are source snapshots, separate from the data distributed as release assets.

- [German: source and modification notice](de-DE/README.md)
- [French: source](fr-FR/README.md)
- [Polish: original DAT and upstream OXT provenance](pl-PL/README.md)
- [Slovak: source and modification notice](sk-SK/README.md)

To reproduce the derived DATs, use Python 3.9+ and gzip. From the repository root:

```sh
work=$(mktemp -d)
for locale in de-DE sk-SK; do
  gzip -dc "corresponding-source/$locale/source-original.dat.gz" > "$work/$locale-original.dat"
  python3 corresponding-source/derive_mythes.py \
    "$work/$locale-original.dat" "$work/${locale}_thesaurus.dat"
done
sha256sum "$work/de-DE_thesaurus.dat" "$work/sk-SK_thesaurus.dat"
```

Compare the results with the [catalog](../catalog/thesauri.json). Copyright, license and dated modifications are documented in [licenses](../licenses/README.md).
