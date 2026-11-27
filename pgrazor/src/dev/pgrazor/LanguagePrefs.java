package dev.pgrazor;

import java.util.Locale;

/** PGS interface languages only. Never changes the process or the game's Locale. */
public final class LanguagePrefs {
    public static final String KEY="pgsLanguage";
    public static final String SYSTEM="system";
    private static final String[] CODES={SYSTEM,"de","en","es","fr","pt-BR","ru","it","zh-Hant","nl","th","ko"};
    private static final String[] NAMES={"System","Deutsch","English","Español","Français","Português",
        "Русский","Italiano","繁體中文","Nederlands","ภาษาไทย","한국어"};

    private LanguagePrefs() {}

    /** Stable selector order; callers cannot modify the supported-language list. */
    public static String[] codes(){return CODES.clone();}

    /** Strict canonical validation for explicit choices and imported backups. */
    public static boolean isValid(String code){
        for(String supported:CODES)if(supported.equals(code))return true;
        return false;
    }

    /** Normalize harmless case/separator differences on disk; unknown values follow System. */
    public static String normalize(String code){
        if(code==null)return SYSTEM;
        String tag=code.trim().replace('_','-');
        for(String supported:CODES)if(supported.equalsIgnoreCase(tag))return supported;
        return SYSTEM;
    }

    /** Native language names; the UI translates the special "System" label itself. */
    public static String nativeName(String code){
        String normalized=normalize(code);
        for(int i=0;i<CODES.length;i++)if(CODES[i].equals(normalized))return NAMES[i];
        return NAMES[0];
    }

    /**
     * Resolve a startup choice without mutating Locale. Portuguese variants use pt-BR and
     * Chinese variants use the available traditional translation. Unsupported system
     * languages fall back to English; the saved selection remains "system".
     */
    public static String resolve(String code,Locale systemLocale){
        String selected=normalize(code);
        if(!SYSTEM.equals(selected))return selected;
        String language=systemLocale==null?"":systemLocale.getLanguage();
        if("pt".equals(language))return "pt-BR";
        if("zh".equals(language))return "zh-Hant";
        for(String supported:CODES)if(!SYSTEM.equals(supported)&&supported.equals(language))return supported;
        return "en";
    }
}
