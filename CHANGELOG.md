# CHANGELOG

## v0.3.0 (2026-07-11)

### Feature

* feat: nest provenance and selection into $manifest_schema with resource counts and null-safe jq recipes

- move $source_manifest and selection_used under $manifest_schema (root stays lean)

- add resource_counts: per-resource-type cardinality so agents can size the slice (e.g. tests vs models) before querying

- add jq_guardrails + rewrite jq_recipes null-safe and lean: guard missing keys with // {} and // [], filter lineage walks to models, project single fields instead of dumping nodes

- keep $dbt_ls_selection at root (can run to hundreds of entries on test-heavy projects)

- works identically in --offline mode: counts are computed from the slimmed output itself ([`0e267a6`](https://github.com/luutuankiet/dbt-mp/commit/0e267a6139351ea7cce47da41d2c601293d8010c))

## v0.2.2 (2026-07-11)

### Fix

* fix: force v0.2.2 release to publish to pypi (v0.2.1 tagged but never published) ([`9c72311`](https://github.com/luutuankiet/dbt-mp/commit/9c723119c6721495d0a46454e0c17a7286ac664a))

## v0.2.1 (2026-07-11)

### Unknown

* Add offline mode and improve manifest slicing with columns &amp; relation_name (#3)

Co-authored-by: Claude Opus 4.8 &lt;noreply@anthropic.com&gt;
Co-authored-by: Claude &lt;noreply@anthropic.com&gt; ([`82b99fe`](https://github.com/luutuankiet/dbt-mp/commit/82b99fe7a1964cc69e476a9f6b4276240c30d6fe))

## v0.2.0 (2026-02-07)

### Documentation

* docs: add gsd-lite plans ([`275dd5a`](https://github.com/luutuankiet/dbt-mp/commit/275dd5a80cee9f5db550dff3dd2e914f42c22376))

### Feature

* feat: adds jsonschema and debug model list into output ([`667c928`](https://github.com/luutuankiet/dbt-mp/commit/667c9285317dc4267687488888adf5aacabca72d))

### Unknown

* Merge pull request #2 from luutuankiet/feat/add_json_schema

feat: adds jsonschema and debug model list into output ([`a540dce`](https://github.com/luutuankiet/dbt-mp/commit/a540dce3a60c08934573d7d9c5b556817a7dc485))

## v0.1.4 (2026-01-27)

### Fix

* fix: reomove column key from output cause this is not consistently filled by dbt ([`582fdb6`](https://github.com/luutuankiet/dbt-mp/commit/582fdb65fd90870bc61993a4362bb3a33c14947b))

## v0.1.3 (2026-01-27)

### Fix

* fix: bump release ([`5857b9b`](https://github.com/luutuankiet/dbt-mp/commit/5857b9be09d645aa6db6b44b54773413020e07cd))

## v0.1.2 (2026-01-27)

### Fix

* fix: bump release ([`e6ba755`](https://github.com/luutuankiet/dbt-mp/commit/e6ba755489bf3c528d7724e1543c4ed9f6e0c664))

* fix: additional root key to traceback selection syntax used (#1) ([`e0ef0c3`](https://github.com/luutuankiet/dbt-mp/commit/e0ef0c3b144dd9c1a41f1fc9ae65b8e23b341442))

## v0.1.1 (2025-12-21)

### Documentation

* docs: add readme 🚀 ([`7530178`](https://github.com/luutuankiet/dbt-mp/commit/753017894f2c186a879238d6c64d604a8f7a1694))

### Feature

* feat: add pypi distr ([`c982485`](https://github.com/luutuankiet/dbt-mp/commit/c9824859c5a13a29f4c28340779a35c5f29e4538))

* feat: run compile upfront to parse compiled_code ([`0bae521`](https://github.com/luutuankiet/dbt-mp/commit/0bae521fecdbd719cf0c49168875f6ba4be0b85d))

### Fix

* fix: minimal pypi publish ([`181ef62`](https://github.com/luutuankiet/dbt-mp/commit/181ef62ebe41323b692f3619952337628c486797))

### Unknown

* init ([`9d563b6`](https://github.com/luutuankiet/dbt-mp/commit/9d563b6395442f502d3273c0b142f9c6a7fdd522))

* Initial commit ([`c4fa224`](https://github.com/luutuankiet/dbt-mp/commit/c4fa22454fcbdaaea819ed0efb379bb6ca4273ae))
