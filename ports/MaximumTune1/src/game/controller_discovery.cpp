#include "kernel/kernel.h"
// acLib hardware discovery, using the same virtual baseboard/controller
// boundary as the standalone Sega Golf port. The original initialization,
// storage, input readers and game startup checks remain in the guest.
X86_FUNC(sub_000B6E00) {
    if (kernel::R32(0x26fd38 - 0x10)) {
        // The original discovery update publishes these version bytes at
        // info+6/+7 and info+0x14/+0x15. State 4 is its idle/ready state.
        kernel::G<uint8_t>(0x26fd38 + 0x1c + 6) = 1;
        kernel::G<uint8_t>(0x26fd38 + 0x1c + 7) = 1;
        kernel::G<uint8_t>(0x26fd38 + 0x1c + 0x14) = 0x12;
        kernel::G<uint8_t>(0x26fd38 + 0x1c + 0x15) = 0x07;
        kernel::W32(0x26fd38, 4);
        LOG_FIRST(1, "MaximumTune1: virtual baseboard and system controller ready");
    }
    kernel::Return(ctx, 0, 0);
}
