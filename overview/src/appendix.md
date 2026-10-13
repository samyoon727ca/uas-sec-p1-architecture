# Appendix: glossary and sources {- #appendix}

## Glossary {-}

| Term | Meaning in this document |
|---|---|
| A/B layout | Two copies of the boot chain or image on storage, so a device can fall back to the previous one if a new one fails |
| authPolicy | The policy digest a TPM object requires before it can be used ([](#c-policy)) |
| Bank (PCR) | One set of PCRs for one hash algorithm; P2's policy uses the SHA-256 bank |
| BL31 | The runtime stage of Arm Trusted Firmware (TF-A), loaded with U-Boot in `u-boot.itb` on the i.MX 8M Plus |
| Boot ROM | Code in the SoC's mask ROM that runs first at power-on and cannot be changed |
| `bootm` | The U-Boot command that boots an image; with measured boot it also extends the PCRs |
| C2 | Command and control of the vehicle |
| CC | Companion computer (P1 CMP-CC): the vehicle's Linux computer; in P2 a DEBIX Model A |
| CSF, CST | Command Sequence File and NXP's Code-Signing Tool that produces it, for HAB ([](#c-hab)) |
| Devicetree | A data structure describing hardware to the boot loader and kernel; also the binary format FIT images use |
| dm-verity | A Linux mechanism that checks every block of a read-only filesystem against a hash tree (P4's SR-006) |
| ECSPI | The i.MX SPI controller; the DEBIX's TPM would sit on ECSPI2 |
| Ed25519 | The signature scheme PX4's secure boot uses: 32-byte public keys, 64-byte signatures |
| Epoch | P2's anti-rollback number, kept as bits in a TPM NV index ([](#c-epoch)) |
| ESAPI | The Enhanced System API of the TPM software stack (tpm2-tss), used by `p2-unseal` |
| Event log | The record of every PCR extend, which replays to the PCR values ([](#c-pcr)) |
| Extend | The only way to change a PCR: new = H(old ‖ digest) |
| FC | Flight controller (P1 CMP-FC): PX4 on a Pixhawk 6X |
| FIT | Flattened Image Tree, U-Boot's signed multi-image format ([](#c-fit)) |
| Fuse (eFuse, OTP) | One-time-programmable bits in the SoC; burning one is permanent |
| GCS | Ground control station (P1 CMP-GCS) |
| HAB | High Assurance Boot, NXP's boot-ROM verification ([](#c-hab)) |
| HSM | Hardware security module: a device that holds private keys and signs without exporting them |
| initramfs | The small root filesystem the kernel starts first; in P2 it holds `p2-unseal` |
| MAVLink | The command and telemetry protocol between GCS, CC and FC; MAVLink 2 can sign frames |
| MSS | Maintenance and support station (P1 CMP-MSS): builds, signs and provisions |
| Name (TPM) | The digest of a TPM object's public area, used to identify it in policies |
| NV index | A small area of TPM non-volatile memory with its own type and authorization |
| PCR | Platform Configuration Register, a TPM register changed only by extend ([](#c-pcr)) |
| PKCS#11 | The standard API through which software asks an HSM to sign |
| Policy session | A TPM session in which policy commands build a digest that must match an object's authPolicy ([](#c-policy)) |
| PolicyAuthorize | A policy command that accepts any policy signed by a named key ([](#c-authorize)) |
| policyRef | A string signed together with an approved policy, naming its use (`p2/cc-keys`) |
| QEMU `virt` | QEMU's generic Arm machine, used for the emulated CC |
| Salted session | A TPM session whose key derives from a secret encrypted to a TPM-resident key ([](#c-session)) |
| Sealing | Storing a secret under a TPM so that it is released only when a policy is satisfied ([](#c-seal)) |
| SITL | PX4 software-in-the-loop simulation (P3's harness) |
| SoC | System-on-chip; the i.MX 8M Plus on the CC |
| SPL | U-Boot's secondary program loader, the first stage the i.MX boot ROM loads |
| SRK | Super Root Key; HAB's table of up to four root public keys, whose hash is fused |
| STRIDE | Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege |
| swtpm | A software TPM 2.0 emulator; P2's CI uses swtpm 0.7.3 |
| SWD | Serial Wire Debug, the STM32's debug port, used to flash the boot loader |
| TOC | The table of contents in a PX4 secure-boot image ([](#c-px4)) |
| TPM | Trusted Platform Module, TPM 2.0 in P2 |
| U-Boot | The open-source boot loader P2 uses, release `v2026.07` |
| WireGuard | The VPN tunnel between GCS and CC (P1 DD-02) |

## Sources {-}

**The two repositories, at the commits this document was built from** (see [](#built-from)):

- P1: <https://github.com/samyoon727ca/uas-sec-p1-architecture>, data at `{{p1.data_commit_full}}`. Documents cited: `README.md`, `data/README.md`, `docs/01-system-description.md` to `docs/08-verification-plan.md`, `docs/references.md`, `.github/workflows/validate.yml`.
- P2: <https://github.com/{{p2.repo}}> at `{{p2.commit_full}}`. Documents cited: `README.md`, `docs/01-scope-and-trace.md` to `docs/06-verification.md`, `docs/references.md`, `evidence/README.md`, `tests/ve07/README.md`, `tests/ve08/README.md`, and the source files cited by line.

**External sources,** as P2 pins and cites them (P2 `docs/references.md`; versions and hashes are P2's):

| Tag | Source | Version P2 pins |
|---|---|---|
| [UBOOT] | U-Boot release tarball `u-boot-2026.07.tar.bz2` | `v2026.07`, SHA-256 `78e8bfc382fe388f9b55aa1daf8c563522a037779b5d4c349d1415e381f1243e` |
| [UBOOT-SIG] | U-Boot `doc/usage/fit/signature.rst`, `doc/usage/fit/sign-configs.rst` | `v2026.07` |
| [UBOOT-MB] | U-Boot `doc/usage/measured_boot.rst` | `v2026.07` |
| [UBOOT-HAB] | U-Boot `doc/imx/habv4/` | `v2026.07` |
| [NXP-CST] | NXP Code-Signing Tool User's Guide | Rev. 3.3.1 |
| [NXP-FUSE] | NXP `uboot-imx` `doc/imx/habv4/guides/mx8m_secure_boot.txt` | commit `bb41975a` |
| [TCG-P1], [TCG-P2] | TCG TPM 2.0 Library, Part 1 (Architecture) and Part 2 (Structures) | Revision 01.59 |
| [SP800-57] | NIST SP 800-57 Part 1 Rev. 5 | May 2020 |
| [PX4-SECBOOT], [PX4-BL] | PX4 Guide: Bootloader Secure Boot; PX4-Autopilot boot-loader source | `v1.18.0-rc1`, commit `fca3df86` |
| [SWTPM] | swtpm | 0.7.3 (Ubuntu `0.7.3-0ubuntu5.24.04.1`) |
| [TPM2-TSS], [TPM2-TOOLS] | tpm2-tss ESAPI; tpm2-tools | 4.0.1; 5.6 |
| [QEMU] | QEMU `hw/arm/virt.c`, `hw/core/sysbus-fdt.c` | `v8.2.2` |
