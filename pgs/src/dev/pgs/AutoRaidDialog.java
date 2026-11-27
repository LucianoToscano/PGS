package dev.pgs;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.graphics.drawable.ColorDrawable;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * "Auto-Raid" settings dialog in the Automation section. Edits a detached {@link AutoRaidPreferences}
 * draft seeded from the coordinator-owned {@code AutoRaid} controller: every change is validated and
 * persisted through {@link AutoRaid#configure}, and Start hands the draft to {@link AutoRaid#start},
 * which freezes it for the session. Chrome follows {@link MapTheme}; polling and the dialog stay scoped
 * through {@link DialogLifecycle}, refreshing the visible status once a second. While a session runs the
 * configuration controls are disabled so the running settings cannot change underneath it.
 */
public final class AutoRaidDialog {
    private AutoRaidDialog() {}

    public static void show(Activity activity) {
        if (activity == null || activity.isFinishing() || activity.isDestroyed()) return;
        Context ui = MapTheme.wrap(activity);
        LinearLayout body = new LinearLayout(ui); body.setOrientation(LinearLayout.VERTICAL);
        int pad = MapTheme.dp(ui, 16); body.setPadding(pad, pad, pad, pad);

        // The draft is this dialog's own working copy; the controller keeps the authoritative one.
        final AutoRaidPreferences draft = AutoRaid.preferences();
        final org.json.JSONObject[] names = {null};

        TextView description = new TextView(ui);
        description.setText(I18n.t("Finds the nearest matching raid the game has loaded, travels there, waits for enough players, "
            + "then battles using your raid auto-attack settings and catches the boss. Stops at the raid limit, after a shiny "
            + "is caught if selected, or after two consecutive losses. Stop ends the session after its current raid."));
        body.addView(description);

        TextView status = new TextView(ui); body.addView(status);

        final TextView tiers = button(body, "");
        final TextView bosses = button(body, "");
        final TextView maxRaids = button(body, "");
        final TextView minPlayers = button(body, "");
        final TextView waitSeconds = button(body, "");
        final TextView travel = button(body, "");
        final TextView distance = button(body, "");

        final CheckBox stopShiny = new CheckBox(ui);
        stopShiny.setText(I18n.t("Stop after catching a shiny (it still counts toward the maximum)")); body.addView(stopShiny);
        final CheckBox freePass = new CheckBox(ui);
        freePass.setText(I18n.t("Use the free daily raid pass")); body.addView(freePass);
        final CheckBox premiumPass = new CheckBox(ui);
        premiumPass.setText(I18n.t("Use Premium Battle passes")); body.addView(premiumPass);
        TextView passNote = new TextView(ui);
        passNote.setText(I18n.t("Uses an allowed free pass before a Premium Battle Pass. Remote Raid Passes are never used."));
        body.addView(passNote);

        final CheckBox razzBerry = new CheckBox(ui);
        razzBerry.setText(I18n.t("Use a Razz Berry on bonus catches")); body.addView(razzBerry);
        final CheckBox goldenRazzBerry = new CheckBox(ui);
        goldenRazzBerry.setText(I18n.t("Use a Golden Razz Berry on bonus catches")); body.addView(goldenRazzBerry);
        TextView berryNote = new TextView(ui);
        berryNote.setText(I18n.t("Golden Razz takes priority and falls back to Razz when unavailable. Leave both unchecked to use no berries. "
            + "Auto-Raid uses Excellent curveballs with Always Hit (never miss). Pokémon can still break out."));
        body.addView(berryNote);

        final Button start = new Button(ui); start.setAllCaps(false); start.setText(I18n.t("Start")); body.addView(start);
        final Button stop = new Button(ui); stop.setAllCaps(false); stop.setText(I18n.t("Stop")); body.addView(stop);

        final boolean[] refreshing = {false};
        final View[] config = {tiers, bosses, maxRaids, minPlayers, waitSeconds, travel, distance, stopShiny, freePass, premiumPass, razzBerry, goldenRazzBerry};
        final Runnable update = () -> {
            refreshing[0] = true;
            boolean running = AutoRaid.running();
            status.setText(AutoRaid.status());
            tiers.setText(I18n.format("Raid tiers: %1$s", String.valueOf((Object)(tierSummary(draft.tierMask)))));
            bosses.setText(I18n.format("Raid bosses: %1$s", String.valueOf((Object)(bossSummary(draft.bosses, names[0])))));
            maxRaids.setText(I18n.format("Maximum raids: %1$s", String.valueOf((Object)(draft.maxRaids))));
            minPlayers.setText(I18n.format("Minimum players in lobby: %1$s", String.valueOf((Object)(draft.minPlayers))));
            waitSeconds.setText(I18n.format("Lobby wait: %1$s s", String.valueOf((Object)(draft.waitSeconds))));
            travel.setText(I18n.format("Travel to raids: %1$s", String.valueOf((Object)((draft.walk ? I18n.t("Walk") : I18n.t("Teleport"))))));
            distance.setText(I18n.format("Stay within: %1$s", I18n.t(AutoRaidPreferences.distanceSummary(draft.maxDistanceKm))));
            stopShiny.setChecked(draft.stopOnShiny);
            freePass.setChecked(draft.freePass);
            premiumPass.setChecked(draft.premiumPass);
            razzBerry.setChecked(draft.razzBerry);
            goldenRazzBerry.setChecked(draft.goldenRazzBerry);
            for (View v : config) SettingsUi.enabled(v, !running);
            start.setEnabled(!running);
            stop.setEnabled(running);
            refreshing[0] = false;
        };

        tiers.setOnClickListener(v -> tierPicker(activity, draft, update));
        bosses.setOnClickListener(v -> bossInput(activity, draft, update));
        maxRaids.setOnClickListener(v -> intInput(activity, draft, update, I18n.format("Maximum completed raids (%1$s-%2$s)", String.valueOf((Object)(AutoRaidPreferences.MAX_RAIDS_MIN)), String.valueOf((Object)(AutoRaidPreferences.MAX_RAIDS_MAX))),
            AutoRaidPreferences.MAX_RAIDS_MIN, AutoRaidPreferences.MAX_RAIDS_MAX, draft.maxRaids, n -> draft.maxRaids = n));
        minPlayers.setOnClickListener(v -> intInput(activity, draft, update, I18n.format("Minimum players in lobby (%1$s-%2$s)", String.valueOf((Object)(AutoRaidPreferences.MIN_PLAYERS_MIN)), String.valueOf((Object)(AutoRaidPreferences.MIN_PLAYERS_MAX))),
            AutoRaidPreferences.MIN_PLAYERS_MIN, AutoRaidPreferences.MIN_PLAYERS_MAX, draft.minPlayers, n -> draft.minPlayers = n));
        waitSeconds.setOnClickListener(v -> intInput(activity, draft, update, I18n.format("Lobby wait in seconds (%1$s-%2$s)", String.valueOf((Object)(AutoRaidPreferences.WAIT_MIN)), String.valueOf((Object)(AutoRaidPreferences.WAIT_MAX))),
            AutoRaidPreferences.WAIT_MIN, AutoRaidPreferences.WAIT_MAX, draft.waitSeconds, n -> draft.waitSeconds = n));
        travel.setOnClickListener(v -> travelPicker(activity, draft, update));
        distance.setOnClickListener(v -> distancePicker(activity, draft, update));
        stopShiny.setOnCheckedChangeListener((v, on) -> { if (!refreshing[0]) { draft.stopOnShiny = on; apply(activity, draft, update); } });
        freePass.setOnCheckedChangeListener((v, on) -> { if (!refreshing[0]) { draft.freePass = on; apply(activity, draft, update); } });
        premiumPass.setOnCheckedChangeListener((v, on) -> { if (!refreshing[0]) { draft.premiumPass = on; apply(activity, draft, update); } });
        razzBerry.setOnCheckedChangeListener((v, on) -> { if (!refreshing[0]) { draft.razzBerry = on; apply(activity, draft, update); } });
        goldenRazzBerry.setOnCheckedChangeListener((v, on) -> { if (!refreshing[0]) { draft.goldenRazzBerry = on; apply(activity, draft, update); } });

        start.setOnClickListener(v -> {
            try { AutoRaid.start(draft); }
            catch (IllegalArgumentException | IllegalStateException refused) { toast(activity, refused.getMessage()); }
            update.run();
        });
        stop.setOnClickListener(v -> { AutoRaid.stop(); update.run(); });

        update.run();
        ScrollView scroll = new ScrollView(ui); scroll.addView(body);
        AlertDialog dialog = new AlertDialog.Builder(ui).setTitle(I18n.t("Auto-Raid")).setView(scroll)
            .setPositiveButton(I18n.t("Done"), null).create();
        Handler handler = new Handler(Looper.getMainLooper());
        Runnable refresh = new Runnable() {
            public void run() { if (dialog.isShowing()) { update.run(); handler.postDelayed(this, 1000); } }
        };
        DialogLifecycle.bind(activity, dialog, () -> handler.removeCallbacks(refresh));
        dialog.setOnShowListener(d -> {
            MapTheme.style(body); MapTheme.styleButtons(dialog);
            dialog.getWindow().setBackgroundDrawable(new ColorDrawable(MapTheme.surface()));
            handler.post(refresh);
        });
        dialog.show();
        new Thread(() -> {
            org.json.JSONObject loaded = PokemonSpeciesDialog.readNames(activity);
            activity.runOnUiThread(() -> {
                if (!dialog.isShowing() || activity.isFinishing() || activity.isDestroyed()) return;
                names[0] = loaded;
                update.run();
            });
        }, "pgrazor-raid-names").start();
    }

    /** Persists the current draft through the controller, reporting any rejection without changing it. */
    private static void apply(Activity activity, AutoRaidPreferences draft, Runnable update) {
        try { AutoRaid.configure(draft); }
        catch (IllegalArgumentException | IllegalStateException refused) {
            java.util.Properties saved = new java.util.Properties();
            AutoRaid.preferences().write(saved); draft.read(saved);
            toast(activity, refused.getMessage());
        }
        update.run();
    }

    private interface IntSetter { void set(int value); }

    private static void intInput(Activity a, AutoRaidPreferences draft, Runnable update,
                                 String title, int min, int max, int current, IntSetter save) {
        Context ui = MapTheme.wrap(a);
        EditText edit = new EditText(ui); edit.setSingleLine(true); edit.setText(String.valueOf(current));
        edit.setInputType(InputType.TYPE_CLASS_NUMBER);
        AlertDialog d = new AlertDialog.Builder(ui).setTitle(title).setView(edit)
            .setPositiveButton(I18n.t("Save"), null).setNegativeButton(I18n.t("Cancel"), null).create();
        DialogLifecycle.bind(a, d, null);
        d.setOnShowListener(x -> { MapTheme.style(edit); MapTheme.styleButtons(d);
            d.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w -> {
                try {
                    int n = Integer.parseInt(edit.getText().toString().trim());
                    if (n < min || n > max) throw new NumberFormatException();
                    save.set(n); apply(a, draft, update); d.dismiss();
                } catch (NumberFormatException e) { edit.setError(I18n.format("Enter a whole number from %1$s to %2$s.", String.valueOf((Object)(min)), String.valueOf((Object)(max)))); }
            });
        });
        d.show();
    }

    private static void bossInput(Activity a, AutoRaidPreferences draft, Runnable update) {
        // Auto-Raid's picker: category browsing + bulk select, saving only the canonical boss Dex IDs.
        PokemonSpeciesDialog.showRaid(a, I18n.t("Raid bosses"), I18n.t("bosses"), AutoRaidPreferences.MAX_BOSSES,
            () -> draft.bosses, value -> {
                draft.bosses = AutoRaidPreferences.normalizeBosses(value);
                apply(a, draft, update);
            }, null, I18n.t("Any boss (no selection)"));
    }

    private static String bossSummary(String bosses, org.json.JSONObject names) {
        if (bosses == null || bosses.isEmpty()) return I18n.t("Any");
        String[] ids = bosses.split(",");
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < Math.min(3, ids.length); i++) {
            if (i > 0) out.append(", ");
            String name = names == null ? "" : names.optString(ids[i], "");
            out.append(name.isEmpty() ? "#" + ids[i] : name);
        }
        if (ids.length > 3) out.append(I18n.format(" +%1$s more",ids.length-3));
        return out.toString();
    }

    /** Only the visible labels change; tier bits and stored preferences stay canonical. */
    private static String tierSummary(int mask) {
        if ((mask & AutoRaidPreferences.TIER_MASK_ALL) == 0) return I18n.t("Any tier");
        StringBuilder out = new StringBuilder();
        for (int i=0;i<AutoRaidPreferences.TIER_LABELS.length;i++) if ((mask & (1<<i)) != 0) {
            if (out.length()>0) out.append(", ");
            out.append(I18n.t(AutoRaidPreferences.TIER_LABELS[i]));
        }
        return out.toString();
    }

    private static void tierPicker(Activity a, AutoRaidPreferences draft, Runnable update) {
        Context ui = MapTheme.wrap(a);
        LinearLayout body = new LinearLayout(ui); body.setOrientation(LinearLayout.VERTICAL);
        TextView help = new TextView(ui);
        help.setText(I18n.t("Select the raid tiers to join. Select none to join any tier.")); body.addView(help);
        final int[] mask = {draft.tierMask};
        for (int i = 0; i < AutoRaidPreferences.TIER_LABELS.length; i++) {
            final int bit = 1 << i;
            CheckBox row = new CheckBox(ui); row.setText(I18n.t(AutoRaidPreferences.TIER_LABELS[i]));
            row.setChecked((mask[0] & bit) != 0);
            row.setOnCheckedChangeListener((v, on) -> { if (on) mask[0] |= bit; else mask[0] &= ~bit; });
            body.addView(row);
        }
        ScrollView scroll = new ScrollView(ui); scroll.addView(body);
        AlertDialog d = new AlertDialog.Builder(ui).setTitle(I18n.t("Raid tiers")).setView(scroll)
            .setPositiveButton(I18n.t("Save"), null).setNegativeButton(I18n.t("Cancel"), null).create();
        DialogLifecycle.bind(a, d, null);
        d.setOnShowListener(x -> { MapTheme.style(body); MapTheme.styleButtons(d);
            d.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                draft.tierMask = mask[0]; apply(a, draft, update); d.dismiss();
            });
        });
        d.show();
    }

    private static void travelPicker(Activity a, AutoRaidPreferences draft, Runnable update) {
        Context ui = MapTheme.wrap(a);
        AlertDialog d = new AlertDialog.Builder(ui).setTitle(I18n.t("Travel to raids"))
            .setNegativeButton(I18n.t("Cancel"), null).create();
        ChoiceList.attach(d, new String[]{
            I18n.t("Teleport\nJump straight to the raid"),
            I18n.t("Walk\nMove there at walking speed")
        }, index -> { draft.walk = index == 1; apply(a, draft, update); });
        DialogLifecycle.bind(a, d, null);
        d.setOnShowListener(x -> { MapTheme.styleButtons(d);
            d.getWindow().setBackgroundDrawable(new ColorDrawable(MapTheme.surface()));
        });
        d.show();
    }

    private static void distancePicker(Activity a, AutoRaidPreferences draft, Runnable update) {
        Context ui = MapTheme.wrap(a);
        AlertDialog d = new AlertDialog.Builder(ui).setTitle(I18n.t("Stay within"))
            .setNegativeButton(I18n.t("Cancel"), null).create();
        final int[] choices = AutoRaidPreferences.DISTANCE_CHOICES_KM;
        String[] labels = new String[choices.length];
        for (int i = 0; i < choices.length; i++)
            labels[i] = choices[i] == 0 ? I18n.t("No limit\nJoin the nearest raid wherever it is")
                : I18n.format("%1$s km\nOnly raids within %1$s km of where you press Start",choices[i]);
        ChoiceList.attach(d, labels, index -> { draft.maxDistanceKm = choices[index]; apply(a, draft, update); });
        DialogLifecycle.bind(a, d, null);
        d.setOnShowListener(x -> { MapTheme.styleButtons(d);
            d.getWindow().setBackgroundDrawable(new ColorDrawable(MapTheme.surface()));
        });
        d.show();
    }

    private static TextView button(LinearLayout body, String text) {
        Button b = new Button(body.getContext()); b.setText(text); b.setAllCaps(false); body.addView(b); return b;
    }

    private static void toast(Activity activity, String message) {
        Toast.makeText(activity, message == null || message.isEmpty() ? I18n.t("Could not update Auto-Raid.") : message,
            Toast.LENGTH_SHORT).show();
    }
}
