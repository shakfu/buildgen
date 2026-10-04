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
  description: "A blog built with Quarto"
  # Required for the RSS feed: set to the deployed URL.
  site-url: https://example.com
  navbar:
    right:
      - about.qmd
      - icon: rss
        href: index.xml

format:
  html:
    theme:
      - cosmo
      - brand
    css: styles.css
