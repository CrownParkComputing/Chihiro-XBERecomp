#include "xdk/d3d8.h"
#include "kernel/kernel.h"
X86_EXTERN_FUNC(__imp__sub_00170600);
// Startup submits an empty visibility query at 0x4d810 and polls it at
// 0x4d829 before presenting. Submit the guest commands and let the renderer
// complete the real report before executing the original result reader.
X86_FUNC(sub_00170600) {
    d3d::FlushGuestCommands();
    __imp__sub_00170600(ctx, base);
}
