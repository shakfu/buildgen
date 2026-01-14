# TODO

## Extended Recipes

- [ ] Testing recipes: `cpp/catch2`, `cpp/gtest`
- [ ] GUI recipes: `cpp/qt`, `c/gtk`
- [ ] Mixed recipes: `cpp/pybind11-catch2` (extension + tests)

## New Language Categories

- [ ] Rust: `rust/executable`, `rust/lib`, `rust/py-pyo3`
- [ ] Go: `go/executable`, `go/lib`
- [ ] Multi-language projects

## Open Questions

1. **Recipe depth**: Should recipes support more than two levels? (e.g., `cpp/lib/static` vs `cpp/static`)

   > Two-tier is sufficient for now

2. **Compound recipes**: How to handle combinations like pybind11 + catch2 testing?
   - Option A: `py/pybind11-catch2` (explicit compound recipe)
   - Option B: `py/pybind11 --with catch2` (modifier flag)
   - Option C: Separate test recipe that integrates
   
   > It will be impossible to implement configuration for all build variants from the command-line. It is better to generate a recipe which includes options: i.e. a configuragable recipe, which requires further input from the user.

3. **Recipe aliases**: Should common recipes have short aliases?
   ```bash
   buildgen project init -n myapp -r cppexe  # alias for cpp/executable
   ```

   > No

4. **User-defined recipes**: Allow users to define custom recipes in `~/.buildgen/recipes/`?

   > Yes

5. **Recipe metadata**: Should recipes include metadata like author, version, tags?
   ```yaml
   # templates/cpp/executable/recipe.yaml
   name: cpp/executable
   description: C++ executable project
   tags: [c++, cmake, console]
   ```

   > No

6. **Environment options**: How do `--env uv/venv` fit with recipes?
   - Keep as separate flag (orthogonal to recipe)
   - Encode in recipe: `py/pybind11-uv` vs `py/pybind11-venv`

   > The default should be `uv`, but see above, this can be changed by the user to `venv` at the recipe level.

