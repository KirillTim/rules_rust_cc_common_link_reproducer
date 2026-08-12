load("@rules_cc//cc:cc_toolchain_config_lib.bzl", "feature")
load("@rules_cc//cc/common:cc_common.bzl", "cc_common")
load("@rules_cc//cc/toolchains:cc_toolchain_config_info.bzl", "CcToolchainConfigInfo")

def _dummy_cc_toolchain_config_impl(ctx):
    return cc_common.create_cc_toolchain_config_info(
        ctx = ctx,
        toolchain_identifier = "dummy-cc-toolchain",
        host_system_name = "local",
        target_system_name = "local",
        target_cpu = "k8",
        target_libc = "unknown",
        compiler = "clang",
        abi_version = "unknown",
        abi_libc_version = "unknown",
        features = [
            feature(name = "static_link_cpp_runtimes", enabled = True),
            feature(name = "supports_dynamic_linker", enabled = True),
        ],
    )

dummy_cc_toolchain_config = rule(
    implementation = _dummy_cc_toolchain_config_impl,
    provides = [CcToolchainConfigInfo],
)
