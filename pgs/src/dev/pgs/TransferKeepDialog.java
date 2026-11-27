package dev.pgs;

import android.app.Activity;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** Transfer and evolve-before-transfer use independent settings through the shared species picker. */
public final class TransferKeepDialog {
    private TransferKeepDialog() {}

    public static void show(Activity activity, Runnable onSaved) {
        PokemonSpeciesDialog.show(activity, I18n.t("Custom keep list"), I18n.t("species"), 2000,
            Control::transferKeepSpecies, Control::setTransferKeepSpecies, onSaved,
            I18n.t("No extra species protected"), null);
    }

    public static void show(Activity activity, String title, String countNoun,
                            Supplier<String> seed, Consumer<String> commit, Runnable onSaved) {
        PokemonSpeciesDialog.show(activity, title, I18n.t("species"), 2000, seed, commit, onSaved,
            I18n.t("No species selected"), null);
    }
}
