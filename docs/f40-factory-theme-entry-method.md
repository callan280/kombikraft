# F40 factory theme entry method

The target is a custom layout loaded and controlled by the factory KOMBI scene
owner. A separately published Ramses scene can show graphics on the cluster,
but it does not bind the factory speed, RPM, gear or warning controllers. A
parked visual preview has demonstrated fit only. It is not factory theme
activation.

This note records bounded findings from matching version 160.002.002 firmware
and a parked F40 M135i session on 12 November 2026. It is an entry-method
investigation, not an installation guide or a flashable package. The exact
firmware, vehicle captures, identities and analysis artifacts remain private.

## Factory scene selection

Original scene-selection code has six Main asset families: standard BMW
combustion, BMW M Performance, BMW PHEV, BMW BEV, M GmbH and Alpina. Their
Init/Main scene IDs are 99/100. Controlled offline coding fixtures select the
expected family files. The internal coding fields used by those fixtures have
not been mapped to the car's raw CAFD/NCD, and the selected family on this car
has not been proved by that fixture.

The normal owner loader takes a local scene ID and uses the installed scene
configuration. A second owner-local loader accepts scene and resource
filenames. In the 13 recovered GSS source banks, the direct-call search found
one caller of that filename loader: the vehicle-model resource path. The
original resource-ID lookup recognized only IDs `0x100`, `0x101` and `0x104`
across 65,540 offline inputs. These findings do not establish an external
filename command; indirect callers and other interfaces remain to be checked.

## Asset acceptance

The recovered GSS asset software package declares RSA-2048/SHA-256 signing.
The other recovered SWFL components declare the same. The extracted Alpina
Init/Main scenes, resources and shader caches have a second signature layer in
`ASL_Signature.bin`: all eight originals verified, while a one-bit edited Main
control did not. The original verifier hashes cached asset bytes. Its mismatch
path calls error `0x13` and a display-buffer handler. Offline execution of that
handler filled 1920×720 pixels with `0xff808080`; live display and recovery
behaviour have not been established. Editing a BMW programming package or
renaming a scene is therefore not a proven way to install a custom layout.

Original cached-file code rejects `wb` paths to Alpina assets under
`/eMMCgp1/`; an `/eMMCgp2/` positive control passed only that prefix check in
an isolated replay. Reads may return raw-repository cached bytes before opening
the filesystem. The MGU session exposed no `/eMMCgp1/` or `/eMMCgp2/` mount.
This bounds the observed file path; it does not rule out every programming or
runtime route into the KOMBI.

## MGU and KOMBI entry methods to prove

The MGU has a working app/SSH research route and can publish its own cluster
scene. Its native HMI menu integration and the bridge to KOMBI factory scene
ownership remain separate, unresolved entry methods. MGU file access alone
does not write KOMBI assets or attach factory controllers.

For a factory-bound custom theme, the project needs a demonstrated KOMBI entry
method that accepts a modified scene in the original owner, preserves
controller-facing objects and warnings, and handles signature/cache lifecycle.
An authentic BMW programming tool can deliver signed BMW packages; it does not
by itself make modified assets acceptable. Any candidate should first pass an
isolated original-code replay with an edited asset and a controlled restore
path. A live installation remains disabled until that route and recovery are
verified.

Current status: **no demonstrated factory-bound custom-theme entry method**.
Further layout work remains useful for design, but does not close this gate.
