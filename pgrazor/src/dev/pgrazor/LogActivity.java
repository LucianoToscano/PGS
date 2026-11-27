package dev.pgrazor;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

/** Private activity declared in the host APK for user-selected log export. */
public final class LogActivity extends Activity {
    private TextView text;
    private SettingsBackup settingsBackup;
    /**
     * Opens the run log. The patched APK starts this private activity; PGS Root has no manifest
     * entry for it in the untouched game APK, so it shows the same content as an in-game dialog.
     */
    public static void open(Activity activity){
        if(activity==null) return;
        if(PgAssets.rooted()){ RootedLogDialog.show(activity); return; }
        activity.startActivity(new Intent(activity,LogActivity.class));
    }
    @Override public void onBackPressed(){
        if(settingsBackup!=null&&settingsBackup.isBusy())return;
        super.onBackPressed();
    }
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        I18nAndroid.init(getApplication());
        if(getIntent().getBooleanExtra("settingsBackup",false)){
            settingsBackup=new SettingsBackup(this);settingsBackup.show();return;
        }
        LinearLayout layout = new LinearLayout(this); layout.setOrientation(LinearLayout.VERTICAL); layout.setPadding(20,48,20,20);
        TextView heading = new TextView(this); heading.setText(I18n.t("PGS · current run")); heading.setTextSize(22); layout.addView(heading);
        ScrollView scroll = new ScrollView(this); text = new TextView(this); text.setTextIsSelectable(true); scroll.addView(text); layout.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        Button refresh = new Button(this); refresh.setText(I18n.t("Refresh log")); refresh.setOnClickListener(v -> refresh()); layout.addView(refresh);
        TextView detail=new TextView(this);detail.setText(I18n.t("ZIP includes the log and a single-line settings.json snapshot of feature preferences. Login tokens, account data and saved locations are excluded."));layout.addView(detail);
        Button bundle=new Button(this);bundle.setText(I18n.t("Save log + settings (.zip)"));layout.addView(bundle);
        bundle.setOnClickListener(v -> {
            File file=Control.currentLog();if(file==null)return;
            Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/zip");
            intent.putExtra(Intent.EXTRA_TITLE,file.getName().replaceFirst("\\.txt$","")+".zip");startActivityForResult(intent,41);
        });
        Button export = new Button(this); export.setText(I18n.t("Save .txt file")); layout.addView(export);
        export.setOnClickListener(v -> {
            File file = Control.currentLog(); if(file == null) return;
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("text/plain");
            intent.putExtra(Intent.EXTRA_TITLE,file.getName()); startActivityForResult(intent,40);
        });
        Button back = new Button(this); back.setText(I18n.t("Back to controls")); back.setOnClickListener(v -> finish()); layout.addView(back);
        setContentView(layout); refresh();
    }
    private void refresh() {
        File file = Control.currentLog();
        if(file == null) { text.setText(I18n.t("No log file is available. Android logcat may contain startup errors.")); return; }
        try (RandomAccessFile input = new RandomAccessFile(file,"r")) {
            long start = Math.max(0,input.length()-65536); input.seek(start);
            byte[] bytes = new byte[(int)(input.length()-start)]; input.readFully(bytes);
            text.setText((start>0 ? I18n.t("Showing latest 64 KiB. Export saves the current log segment, including retained startup diagnostics.\n") : "") + new String(bytes,StandardCharsets.UTF_8));
        } catch(IOException error) { text.setText(I18n.format("Cannot read log: %1$s", String.valueOf((Object)(error.getMessage())))); }
    }
    protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(settingsBackup!=null){settingsBackup.result(request,result,data);return;}
        if((request!=40&&request!=41) || result!=RESULT_OK || data==null || data.getData()==null || Control.currentLog()==null) return;
        try {
            LogExport.save(this,data.getData(),Control.currentLog(),request==41);
            Toast.makeText(this,request==41?I18n.t("Log and settings saved"):I18n.t("Log saved"),Toast.LENGTH_SHORT).show();
        } catch(IOException error) { Toast.makeText(this,I18n.format("Save failed: %1$s", String.valueOf((Object)(error.getMessage()))),Toast.LENGTH_LONG).show(); }
    }
}
