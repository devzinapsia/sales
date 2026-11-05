# User guide (Knowledge)

End-user guide for this module, in Spanish, packaged for the Zinapsia
`knowledge_transfer` module (repo `zinapsia/knowledge`, ZIP `format_version` 1).

- `knowledge/`: editable source (`manifest.json` + `articles/<key>/body.html`).
- `sale_order_line_pricelist_knowledge.zip`: the ready-to-import package,
  built from `knowledge/`.
- `plan_de_pruebas_sale_order_line_pricelist.docx`: functional test plan
  (Spanish) for validating a new version on a staging branch.

## Import into a database

1. Install `knowledge_transfer` (requires Odoo Enterprise `knowledge`).
2. *Knowledge > Transfer > Import*, upload
   `sale_order_line_pricelist_knowledge.zip`, click *Import*.
3. The articles are created in your private section, under
   `Artículos importados Zinapsia`; move the tree to the workspace you want.
   Importing twice creates two copies.

## Rebuild the ZIP after editing the source

`manifest.json` must be at the root of the ZIP, so don't zip the `knowledge/`
folder itself (nor use Finder's "Compress"). From this `docs/` folder:

```bash
python3 -c "
import pathlib, zipfile
src = pathlib.Path('knowledge')
with zipfile.ZipFile('sale_order_line_pricelist_knowledge.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for p in sorted(src.rglob('*')):
        if p.is_file() and p.name != '.DS_Store':
            zf.write(p, p.relative_to(src).as_posix())
"
```

Bodies may only link to other articles of the package (`kt-article:<key>`);
links to `/odoo/...` records are dropped by the importer.
