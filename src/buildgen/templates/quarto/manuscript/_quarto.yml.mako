project:
  type: manuscript
  # Every page except TODO.md (README.md is excluded by default).
  render:
    - "**/*.qmd"
    - "**/*.md"
    - "!TODO.md"
  output-dir: ${output_dir}

manuscript:
  article: index.qmd

format:
  html:
    comments:
      hypothesis: true
  docx: default
  jats: default
  # Requires a LaTeX distribution (quarto install tinytex).
  # pdf: default

execute:
  freeze: true
