package dev.pgs.root;

/** Fixed-path launch-time switch commands, shared by the installer and the JVM/shell fixtures. */
final class RootToggleCommand {
    private RootToggleCommand() {}
    static final String OK_PREFIX = "PGS_TOGGLE_OK";
    private static final String PATHS = "L=/data/adb/modules/pgs\nU=/data/adb/modules_update/pgs\nF=pgs/injection-off\n"
        + "fail(){ echo PGS_TOGGLE_FAIL=$1; exit 1; }\n";
    static final String LIVE_INJECTION_PROBE =
        "if [ -f /data/adb/modules/pgs/pgs/injection-off ]; then echo MODOFF=1; else echo MODOFF=0; fi";

    static String command(boolean on) {
        String action = on ? "rm -f" : "touch";
        String verify = on ? "[ ! -e" : "[ -f";
        return PATHS
            + "[ -f \"$L/module.prop\" ] || fail not_installed\n"
            + "[ -f \"$L/pgs/toggle-v1\" ] || fail no_toggle_marker\n"
            + "[ ! -e \"$L/disable\" ] || fail disabled\n"
            + "[ ! -e \"$L/remove\" ] || fail removal_pending\n"
            + "if [ -d \"$U\" ]; then [ -d \"$U/pgs\" ] || fail staged_payload_missing; fi\n"
            + action + " \"$L/$F\" || fail write_live\n"
            + "if [ -d \"$U/pgs\" ]; then " + action + " \"$U/$F\" || fail write_staged; fi\n"
            + verify + " \"$L/$F\" ] || fail verify_live\n"
            + "if [ -d \"$U/pgs\" ]; then " + verify + " \"$U/$F\" ] || fail verify_staged; fi\n"
            + "am force-stop com.nianticlabs.pokemongo || fail force_stop\n"
            + "echo " + OK_PREFIX + (on ? "=on\n" : "=off\n");
    }
    static String preserveOffCommand() {
        return PATHS
            + "[ -d \"$U/pgs\" ] || fail no_staged_payload\n"
            + "touch \"$U/$F\" || fail write_staged\n"
            + "[ -f \"$U/$F\" ] || fail verify_staged\n"
            + "echo " + OK_PREFIX + "=preserved_off\n";
    }
    static boolean hasLine(String output, String line) {
        if (output != null) for (String value : output.split("\\r?\\n")) if (line.equals(value.trim())) return true;
        return false;
    }
    static boolean injectionOffFromProbe(String output) { return hasLine(output, "MODOFF=1"); }
    static boolean confirmed(boolean on, String output) { return hasLine(output, OK_PREFIX + (on ? "=on" : "=off")); }
}
