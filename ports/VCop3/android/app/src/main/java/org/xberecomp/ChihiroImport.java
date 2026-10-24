package org.xberecomp;

import android.content.Context;
import android.net.Uri;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.*;
import org.apache.commons.compress.archivers.sevenz.SevenZFile;
import org.apache.commons.compress.archivers.sevenz.SevenZArchiveEntry;

/** Import only the supported extracted Chihiro 7z, without replacing a working install on failure. */
final class ChihiroImport {
    interface Progress { void update(String message); }
    static void run(Context context, Uri uri, Progress progress) throws Exception {
        File work = Files.createTempDirectory(context.getFilesDir().toPath(), "import-").toFile();
        File previous = new File(context.getFilesDir(), "assets.previous");
        File assets = new File(context.getFilesDir(), "assets");
        try {
            File archive = new File(work, "source.7z");
            progress.update("Copying archive…");
            try (InputStream in = context.getContentResolver().openInputStream(uri);
                 OutputStream out = new FileOutputStream(archive)) {
                if (in == null) throw new IOException("Cannot read the selected archive");
                byte[] buffer = new byte[1024 * 1024]; int count;
                while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            }
            try (InputStream in = new FileInputStream(archive)) {
                byte[] magic = new byte[6];
                if (in.read(magic) != 6 || !Arrays.equals(magic, new byte[]{0x37,0x7a,(byte)0xbc,(byte)0xaf,0x27,0x1c}))
                    throw new IOException("Choose a genuine .7z archive");
            }
            File unpacked = new File(work, "unpacked"); unpacked.mkdir();
            Set<String> names = new HashSet<>(); long total = 0; int files = 0;
            try (SevenZFile seven = new SevenZFile(archive)) {
                for (SevenZArchiveEntry entry : seven.getEntries()) {
                    String name = entry.getName();
                    if (name == null || name.isEmpty() || name.startsWith("/") || name.contains("\\") || name.contains(":"))
                        throw new IOException("Unsafe archive path");
                    for (String part : name.split("/")) if (part.equals("..") || part.equals(".")) throw new IOException("Unsafe archive path");
                    if (!names.add(name.toLowerCase(Locale.ROOT))) throw new IOException("Duplicate archive path: " + name);
                    int mode = entry.getWindowsAttributes() >>> 16;
                    if ((mode & 0170000) == 0120000) throw new IOException("Archive links are unsupported");
                    if (!entry.isDirectory()) {
                        if (entry.getSize() < 0 || ++files > 100000 || (total += entry.getSize()) > 12L * 1024 * 1024 * 1024)
                            throw new IOException("Archive exceeds the supported size");
                    }
                }
                byte[] buffer = new byte[1024 * 1024]; SevenZArchiveEntry entry;
                while ((entry = seven.getNextEntry()) != null) {
                    File target = new File(unpacked, entry.getName());
                    if (!target.getCanonicalPath().startsWith(unpacked.getCanonicalPath() + File.separator))
                        throw new IOException("Unsafe archive path");
                    if (entry.isDirectory()) { target.mkdirs(); continue; }
                    progress.update("Extracting " + entry.getName());
                    target.getParentFile().mkdirs();
                    try (OutputStream out = new FileOutputStream(target)) {
                        long written = 0; int count;
                        while ((count = seven.read(buffer)) != -1) { out.write(buffer, 0, count); written += count; }
                        if (written != entry.getSize()) throw new IOException("Incomplete archive entry");
                    }
                }
            }
            ArrayList<File> candidates = new ArrayList<>();
            find(unpacked, PortConfig.executable(context), candidates);
            if (candidates.size() != 1) throw new IOException("Archive must contain exactly one " + PortConfig.executable(context));
            File xbe = candidates.get(0);
            progress.update("Verifying game revision…");
            if (!sha256(xbe).equals(PortConfig.sha256(context))) throw new IOException("This game revision is unsupported. Use " + PortConfig.archive(context));
            File game = xbe.getParentFile();
            String[] required = PortConfig.executable(context).equals("hod3xb.xbe") ? new String[]{"FS", "MVI"} : new String[]{"media"};
            for (String name : required) if (!new File(game, name).isDirectory()) throw new IOException("Missing game folder: " + name);
            delete(previous);
            if (assets.exists()) Files.move(assets.toPath(), previous.toPath(), StandardCopyOption.ATOMIC_MOVE);
            try { Files.move(game.toPath(), assets.toPath(), StandardCopyOption.ATOMIC_MOVE); }
            catch (Exception error) {
                if (previous.exists()) Files.move(previous.toPath(), assets.toPath(), StandardCopyOption.ATOMIC_MOVE);
                throw error;
            }
            if (!context.getSharedPreferences("game", Context.MODE_PRIVATE).edit().putBoolean("verified7z", true).commit())
                throw new IOException("Cannot save import status");
            delete(previous);
        } finally { delete(work); }
    }
    static String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[1024 * 1024]; int count;
            while ((count = in.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        StringBuilder value = new StringBuilder();
        for (byte b : digest.digest()) value.append(String.format(Locale.ROOT, "%02x", b & 255));
        return value.toString();
    }
    private static void find(File dir, String name, List<File> result) {
        File[] children = dir.listFiles(); if (children == null) return;
        for (File child : children) if (child.isDirectory()) find(child, name, result);
        else if (child.getName().equals(name)) result.add(child);
    }
    private static void delete(File file) throws IOException {
        if (!file.exists()) return;
        if (file.isDirectory()) { File[] children = file.listFiles(); if (children != null) for (File child : children) delete(child); }
        Files.delete(file.toPath());
    }
}
