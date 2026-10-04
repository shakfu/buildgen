project:
  type: website
  # Every page except TODO.md (README.md is excluded by default).
  render:
    - "**/*.qmd"
    - "**/*.md"
    - "!TODO.md"
  output-dir: ${output_dir}

website:
  title: "${name}"
  navbar:
    left:
      - href: index.qmd
        text: Home
      - about.qmd

format:
  html:
    theme:
      - cosmo
      - brand
    css: styles.css
    toc: true
