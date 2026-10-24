# Character geometry correction (24 October 2026)

The six Chihiro ports share these renderer corrections:

* Fixed function skinning records and blends all four world matrices for the six Xbox blend modes. Zero-weight bones do not propagate unused NaNs.
* Paired vector MAC and scalar ILU instructions preserve the vector C operand swizzle.
* Smaller offscreen targets retain a sufficiently large shared depth buffer.
* Surface references retain their parent texture and bound textures snapshot the GPU registers.

Ghost Squad before/after captures at the same attract scene show the missing upper arms and thighs restored. This does not establish that every scene in every title is correct.

Validation: all four GPU regressions pass in both Vulkan rendering paths; all three geometry regressions fail against the previous shader code. Surface ownership and binding checks pass against all six SDK copies. Linux and Android builds pass for all six ports.

Maximum Tune 1 and 2 still have an independent black-screen issue after startup; the renderer corrections do not establish playable support for those games.
