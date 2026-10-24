#include "kernel/kernel.h"
#include "core/input.h"
#include "app/app.h"
#include <algorithm>
#include <mutex>

namespace {
std::mutex board_lock;
uint32_t reports = 0;
uint16_t coins = 0;
bool coin_down = false;
void Byte(uint32_t p, uint8_t v) { *static_cast<uint8_t*>(kernel::HostPtr(p)) = v; }
void BigWord(uint32_t p, uint16_t v) { Byte(p, v >> 8); Byte(p + 1, v); }

void UpdateBoard() {
    if (!reports) {
        reports = mem::AllocSystem(64);
        if (!reports) return;
        std::memset(kernel::HostPtr(reports), 0, 64);
        LOGI("MaximumTune1: virtual JVS input board connected");
    }
    // The title's original public capability/report readers use one-based
    // node indices with stride 0xE0. Preserve those readers and their locks.
    const uint32_t node = 0x399a3c + 0xE0;
    Byte(0x399639, 1);
    kernel::W32(0x1a46fc, 0xFF); // test/service switches released (active low)
    kernel::W32(node + 0xAC, reports);
    kernel::W32(node + 0xB0, reports + 8);
    kernel::W32(node + 0xB4, reports + 16);
    Byte(node + 0xCC, 2); // players
    Byte(node + 0xCD, 13); // switches per player
    Byte(node + 0xCE, 2); // coin slots
    Byte(node + 0xCF, 8); // analog channels
    Byte(node + 0xD0, 16); // analog precision
    Byte(node + 0xDA, 8); // output bits
    const auto pad = input::Poll(0);
#ifdef CHIHIRO_SDL_INPUT
    const bool enabled = !app::Unfocused() && !app::GraphicsMenuOpen();
#else
    const bool enabled = true;
#endif
    const bool coin = enabled && (pad.buttons & 0x20);
    if (coin && !coin_down) {
        coins = (coins + 1) & 0x3FFF;
        LOGI("MaximumTune1: coin inserted");
    }
    coin_down = coin;
    BigWord(reports + 8, coins);
    Byte(reports, 0);
    Byte(reports + 1, enabled ? uint8_t(((pad.buttons & 0x10) ? 0x80 : 0) |
        (pad.analog[0] ? 2 : 0) | (true && pad.analog[1] ? 1 : 0)) : 0);
    Byte(reports + 2, enabled && pad.analog[2] ? 0x80 : 0);
    if (true) {
        const int steering = enabled ? pad.lx : 0;
        const int accelerator = enabled ? std::max(int(pad.analog[7]) * 257, std::max(0, int(pad.ly)) * 2) : 0;
        const int brake = enabled ? std::max(int(pad.analog[6]) * 257, std::max(0, -int(pad.ly)) * 2) : 0;
        BigWord(reports + 16, uint16_t(steering + 32768));
        BigWord(reports + 18, uint16_t(std::min(accelerator, 65535)));
        BigWord(reports + 20, uint16_t(std::min(brake, 65535)));
    } else {
        BigWord(reports + 16, uint16_t(enabled ? int(pad.lx) + 32768 : 32768));
        BigWord(reports + 18, uint16_t(enabled ? 32767 - int(pad.ly) : 32768));
    }
}
}

// These original no-argument functions each return a literal pointer. Refresh
// the reports at the same boundary so cached node counts also keep working.
X86_FUNC(sub_00163C30) {
    std::lock_guard guard(board_lock);
    UpdateBoard();
    kernel::Return(ctx, 0x399a3c, 0);
}
X86_FUNC(sub_00163C40) {
    std::lock_guard guard(board_lock);
    UpdateBoard();
    kernel::Return(ctx, 0x399639, 0);
}
