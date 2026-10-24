package org.xberecomp;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.database.Cursor;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.widget.*;
import java.io.File;

public class LauncherActivity extends Activity {
    private TextView status;
    private Button start, choose;
    private ProgressBar progress;
    private boolean importing;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL); layout.setGravity(Gravity.CENTER);
        int padding = (int)(24 * getResources().getDisplayMetrics().density);
        layout.setPadding(padding, padding, padding, padding); layout.setBackgroundColor(0xFF063A59);
        TextView title = new TextView(this); title.setText(getApplicationInfo().loadLabel(getPackageManager()));
        title.setTextSize(28); title.setTextColor(0xFFFFFFFF); layout.addView(title);
        TextView info = new TextView(this);
        info.setText("Import " + PortConfig.archive(this) + " once, then start the game.\nKeep the original .7z as your source. Connect a controller for gamepad controls.");
        info.setTextColor(0xFFDBEFF5); info.setGravity(Gravity.CENTER); layout.addView(info);
        status = new TextView(this); status.setTextColor(0xFFFFFFFF); status.setPadding(0, padding/2, 0, padding/2); layout.addView(status);
        progress = new ProgressBar(this); progress.setVisibility(android.view.View.GONE); layout.addView(progress);
        start = new Button(this); start.setText("Start game"); start.setOnClickListener(v -> launch()); layout.addView(start);
        choose = new Button(this); choose.setText("Import Chihiro .7z"); choose.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT); intent.addCategory(Intent.CATEGORY_OPENABLE); intent.setType("*/*");
            startActivityForResult(intent, 1);
        }); layout.addView(choose);
        if (PortConfig.controls(this).equals("gun-vcop3")) {
            RadioGroup controls = new RadioGroup(this); controls.setOrientation(LinearLayout.HORIZONTAL);
            String selected = getSharedPreferences("game", MODE_PRIVATE).getString("controls", "mouse-controller");
            for (int i = 0; i < 2; i++) {
                final String value = i == 0 ? "mouse-controller" : "controllers";
                RadioButton option = new RadioButton(this); option.setText(i == 0 ? "Touch/mouse + P2 controller" : "Two controllers");
                option.setTextColor(0xFFFFFFFF); option.setId(100+i); controls.addView(option);
                if (selected.equals(value)) controls.check(option.getId());
                option.setOnClickListener(v -> getSharedPreferences("game", MODE_PRIVATE).edit().putString("controls", value).apply());
            } layout.addView(controls);
        }
        Button source = new Button(this); source.setText("Chihiro .7z source"); source.setOnClickListener(v -> startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://archive.org/download/extracted-sega-chihiro-roms")))); layout.addView(source);
        setContentView(layout); update();
    }
    private boolean ready() { return getSharedPreferences("game", MODE_PRIVATE).getBoolean("verified7z", false) && new File(getFilesDir(), "assets/" + PortConfig.executable(this)).isFile(); }
    private void update() { start.setEnabled(!importing && ready()); choose.setEnabled(!importing); if (!importing) status.setText(ready() ? "Game ready" : "Choose the supported .7z archive"); }
    private void launch() {
        if (!ready()) return;
        try { startActivity(new Intent(this, Class.forName(getPackageName()+".GameActivity"))); }
        catch (ClassNotFoundException error) { throw new IllegalStateException(error); }
    }
    @Override protected void onActivityResult(int request, int result, Intent intent) {
        super.onActivityResult(request, result, intent);
        if (request != 1 || result != RESULT_OK || intent == null || intent.getData() == null || importing) return;
        Uri uri = intent.getData(); String name = "";
        try (Cursor cursor = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) name = cursor.getString(0);
        } catch (Exception error) { status.setText("Cannot read the selected file"); return; }
        if (name == null || !name.toLowerCase(java.util.Locale.ROOT).endsWith(".7z")) { status.setText("Choose a .7z archive"); return; }
        importing = true; update(); progress.setVisibility(android.view.View.VISIBLE); status.setText("Preparing import…");
        new Thread(() -> {
            String resultText;
            try { ChihiroImport.run(this, uri, message -> runOnUiThread(() -> { if (!isDestroyed()) status.setText(message); })); resultText = "Game imported and verified. Ready to play."; }
            catch (Exception error) { resultText = "Import failed: " + error.getMessage(); }
            final String message = resultText;
            runOnUiThread(() -> { importing = false; if (isDestroyed()) return; progress.setVisibility(android.view.View.GONE); update(); status.setText(message); });
        }, "Chihiro-import").start();
    }
}
