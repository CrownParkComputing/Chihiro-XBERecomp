#include "kernel/kernel.h"
// OutputDebugStringA: ANSI string descriptor, INT 0x2D/INT3, stdcall ret 4.
// Keep the console's diagnostic text in the host log without a console debugger.
X86_FUNC(sub_0011A2E3) {
    const kernel::Args args{ctx};
    LOGI("MaximumTune2 debug: %s", kernel::ReadCString(args[0]).c_str());
    kernel::Return(ctx, 0, 1);
}
