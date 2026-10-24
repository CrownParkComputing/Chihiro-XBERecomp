#include "kernel/kernel.h"
// Virtual 128 MiB Chihiro media board boot registers. Asset reads remain
// handled by the original game through D: and the host file layer.
X86_FUNC(sub_000B84E0) {
    const kernel::Args a{ctx};
    if (a[0]) {
        kernel::W32(a[0], 0x08000000);
        kernel::W32(a[0] + 4, 0x4D414258); // XBAM
    }
    LOG_FIRST(1, "MaximumTune1: virtual media-board boot signature");
    kernel::Return(ctx, 0, 1);
}
// Virtual command queue boundary. The original acLib allocates its
// request token and consumes the response through its original readers.
// Only the implemented capacity/version/serial commands are acknowledged;
// other commands return the protocol error reply (0x8000).
X86_FUNC(sub_000B9EC0) {
    const kernel::Args a{ctx};
    const uint8_t token = uint8_t(a[0]);
    for (uint32_t i = 0; token && i < 64; ++i) {
        const uint32_t request = 0x3ced80 + i * 0x60;
        if (kernel::G<uint8_t>(request) != token || (kernel::R16(request + 2) & 0x8000)) continue;
        const uint32_t reply = request - 0x20;
        const uint16_t command = kernel::R16(request + 2);
        std::memset(kernel::HostPtr(reply), 0, 0x20);
        kernel::G<uint8_t>(reply) = token;
        uint16_t response = command | 0x8000;
        switch (command) {
        case 0x0001: kernel::W32(reply + 4, 0x08000000); break;
        case 0x0101: kernel::W32(reply + 4, 0x00010001); break;
        case 0x0103: std::memcpy(kernel::HostPtr(reply + 4), "VIRTUAL-000000001", 16); break;
        default: response = 0x8000; break;
        }
        kernel::W16(reply + 2, response);
        LOG_FIRST(24, "MaximumTune1: media command %04X -> %04X", command, response);
        kernel::Return(ctx, 0, 1);
        return;
    }
    kernel::Return(ctx, 1, 1);
}
