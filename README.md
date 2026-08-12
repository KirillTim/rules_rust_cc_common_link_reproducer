# rules_rust cc_common.link reproducer

This analysis-only workspace contains two independent rules_rust reproducers.

1. **Toolchain runtime selection:** Under `--dynamic_mode=fully`, compare a
   `cc_binary` with a `rust_binary` using `experimental_use_cc_common_link = 1`.
   The dummy C++ toolchain supplies `dummy.a` as `static_runtime_lib` and
   `dummy.so` as `dynamic_runtime_lib`. Both rules are expected to link
   `dummy.so`, not `dummy.a`.
2. **Shared `link_deps` runfiles:** Under `--dynamic_mode=off`, pass a
   shared-only `cc_library` through C++ `deps` and Rust `link_deps`. Both rules
   are expected to link `link_dep.so` and include it in their
   `DefaultInfo.default_runfiles`.

Run:

```sh
python3 assert_linkage.py
```

With rules_rust 0.73.0, both use cases reproduce: Rust selects `dummy.a` instead
of `dummy.so`, and Rust links `link_dep.so` without adding it to runfiles.
