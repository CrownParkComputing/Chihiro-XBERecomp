#include "kernel/kernel.h"
#include "xdk/hle.h"
#include "xdk/d3d8.h"
// The original Reset presentation-parameter entry (stdcall ret 4) reaches
// miniport register access. Recreate the host presentation surfaces through
// the existing CreateDevice handler, retaining the shader/resource registries.
X86_FUNC(sub_00167210) {
    const kernel::Args a{ctx};
    const uint32_t parameters = a[0];
    d3d::FlushGuestCommands();
    const uint32_t result = GUEST_CALL(Direct3D_CreateDevice, ctx, {0, 1, 0, 0, parameters, 0});
    LOGI("MaximumTune1: reset host presentation surfaces");
    kernel::Return(ctx, result, 1);
}
