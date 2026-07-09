# Diagrams

Diagram-as-code: the `.mmd` files are the source of truth; the SVGs are
rendered from them with [mermaid-cli](https://github.com/mermaid-js/mermaid-cli)
using `theme.json`.

To re-render after editing a source:

    npx -y @mermaid-js/mermaid-cli -i workflow-hero.mmd -o workflow-hero.svg -c theme.json -b "#0a0a0f"
    npx -y @mermaid-js/mermaid-cli -i run-logic.mmd -o run-logic.svg -c theme.json -b "#0a0a0f"

`theme.json` keeps root-level `htmlLabels: false` so the SVGs use native text
(HTML-labeled SVGs can render blank in some browsers when embedded in a
README).
