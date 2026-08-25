## 🔄 LLM Drift / Curated Documentation Contribution

### 1. Summary of Changes
- **Target Library & Version**: (e.g. Zig v0.16.0, Rust Axum v0.8.1)
- **Document Path**: (e.g. `curated/zig/zig-0.16-faq-troubleshooting.md`)

### 2. Error Diagnostic & Root Cause
- **Error Message**:
```text
<Paste exact compiler / toolchain error here>
```
- **Outdated LLM Pattern**: (Explain what deprecated API or hallucination caused this error)

### 3. Verified Fix & Evidence
- **Compilable Solution**:
```zig / rust / ts
<Paste verified compilable snippet>
```
- **Verification Command & Exit Code**:
  - Command: `zig build` / `cargo test` / `tsc --noEmit`
  - Result: Exit Code 0 (Clean build)

### 4. Privacy & Sanitization Checklist
- [ ] No proprietary business logic included (pure language/framework syntax only)
- [ ] No internal machine paths, secrets, API keys, or personal usernames
- [ ] FTS5 indexed and tested locally with `doc-engine index-file` & `doc-engine search`
