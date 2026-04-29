# Compatibility Notes

This SDK is intentionally staged for migration:

- Lua output is section-ordered to match legacy behavior, but not byte-identical.
- Unknown legacy fields should remain in `extras` until explicitly modeled.
- `GWC` compilation is adapter-driven and can bridge old linker paths.
- Regression checks should prioritize semantic equivalence and runnable artifacts.
