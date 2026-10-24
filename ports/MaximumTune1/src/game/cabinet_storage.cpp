#include "kernel/kernel.h"
#include "app/app.h"
#include <array>
#include <ctime>
#include <fstream>
#include <mutex>

namespace {
std::mutex storage_mutex;
template <size_t N> struct Storage {
    const char* name;
    bool loaded = false;
    std::array<uint8_t, N> bytes;
    explicit Storage(const char* value) : name(value) { bytes.fill(0xFF); }
    std::filesystem::path Path() const { return app::ExeDir() / "hdd" / "cabinet" / name; }
    void Load() {
        if (loaded) return;
        loaded = true;
        std::ifstream input(Path(), std::ios::binary | std::ios::ate);
        if (input && input.tellg() == N) {
            input.seekg(0);
            input.read(reinterpret_cast<char*>(bytes.data()), N);
            if (!input) bytes.fill(0xFF);
        }
    }
    bool Save() const {
        std::error_code error;
        const auto path = Path();
        std::filesystem::create_directories(path.parent_path(), error);
        if (error) return false;
        const auto temporary = path.string() + ".tmp";
        {
            std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
            output.write(reinterpret_cast<const char*>(bytes.data()), N);
            output.flush();
            if (!output) return false;
        }
        std::filesystem::rename(temporary, path, error);
        return !error;
    }
};
Storage<0x2000> eeprom("eeprom.bin");
Storage<0x20000> backup("backup.bin");
Storage<0x10000> firmware("controller-firmware.bin");

template <size_t N>
void Transfer(X86Context& ctx, Storage<N>& storage, bool write) {
    const kernel::Args args{ctx};
    const uint32_t offset = args[0], count = args[1], buffer = args[2];
    if (!buffer || offset > N || count > N - offset) {
        kernel::Return(ctx, kernel::kInvalidParameter, 4);
        return;
    }
    std::lock_guard lock(storage_mutex);
    storage.Load();
    if (write) {
        std::memcpy(storage.bytes.data() + offset, kernel::HostPtr(buffer), count);
        if (!storage.Save()) {
            LOGE("MaximumTune1: cannot persist cabinet %s", storage.name);
            kernel::Return(ctx, 0xC0000185, 4);
            return;
        }
    } else {
        std::memcpy(kernel::HostPtr(buffer), storage.bytes.data() + offset, count);
    }
    LOG_FIRST(24, "MaximumTune1: cabinet %s %s offset %X, %u bytes", storage.name, write ? "write" : "read", offset, count);
    kernel::Return(ctx, 0, 4);
}

void ReadClock(X86Context& ctx) {
    const kernel::Args args{ctx};
    const uint32_t offset = args[0], count = args[1], buffer = args[2];
    if (!buffer || offset > 16 || count > 16 - offset) {
        kernel::Return(ctx, kernel::kInvalidParameter, 4);
        return;
    }
    const auto now = std::time(nullptr);
    std::tm utc{};
    gmtime_r(&now, &utc);
    const auto bcd = [](int value) { return uint8_t((value / 10) * 16 + value % 10); };
    std::array<uint8_t, 16> data{};
    data[0] = bcd(utc.tm_sec); data[1] = bcd(utc.tm_min);
    data[6] = bcd(utc.tm_hour); data[7] = bcd(utc.tm_wday);
    data[8] = bcd(utc.tm_mday); data[9] = bcd(utc.tm_mon + 1);
    data[10] = bcd((utc.tm_year + 1900) % 100); data[11] = bcd((utc.tm_year + 1900) / 100);
    std::memcpy(kernel::HostPtr(buffer), data.data() + offset, count);
    kernel::Return(ctx, 0, 4);
}
} // namespace

// Public JVS APIs use (offset, byte count, buffer, wait flag), stdcall ret 0x10.
// Their original consumers, checksums, firmware initialization and credit logic remain active.
X86_FUNC(sub_001AE210) { Transfer(ctx, eeprom, false); } // JvsEEPROM_Read2
X86_FUNC(sub_001AE3F0) { Transfer(ctx, eeprom, true); } // JvsEEPROM_Write2
X86_FUNC(sub_001AE5D0) { Transfer(ctx, backup, false); } // JvsBACKUP_Read
X86_FUNC(sub_001AE720) { Transfer(ctx, backup, true); } // JvsBACKUP_Write
X86_FUNC(sub_001AD910) { Transfer(ctx, firmware, false); } // JvsScFirmwareDownload2
X86_FUNC(sub_001ADB50) { Transfer(ctx, firmware, true); } // JvsScFirmwareUpload2
X86_FUNC(sub_001AEE80) { ReadClock(ctx); } // JvsRTC_Read2
