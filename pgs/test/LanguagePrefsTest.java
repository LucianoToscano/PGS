package dev.pgs;

import java.util.Arrays;
import java.util.Locale;

/** Pure language matching: no Android resource configuration or process Locale changes. */
public final class LanguagePrefsTest {
    private static void equal(String expected,String actual){
        if(!expected.equals(actual))throw new AssertionError(expected+" != "+actual);
    }
    public static void main(String[] args){
        Locale before=Locale.getDefault();
        String[] expected={"system","de","en","es","fr","pt-BR","ru","it","zh-Hant","nl","th","ko"};
        if(!Arrays.equals(expected,LanguagePrefs.codes()))throw new AssertionError("Selector order changed");
        String[] copy=LanguagePrefs.codes();copy[0]="xx";
        equal("system",LanguagePrefs.codes()[0]);
        for(String code:expected){
            if(!LanguagePrefs.isValid(code)||LanguagePrefs.nativeName(code).isEmpty())throw new AssertionError(code);
            equal(code,LanguagePrefs.normalize(code));
            if(!code.equals("system"))equal(code,LanguagePrefs.resolve(code,Locale.JAPAN));
        }
        equal("System",LanguagePrefs.nativeName("system"));
        equal("Português",LanguagePrefs.nativeName("pt-BR"));
        equal("ภาษาไทย",LanguagePrefs.nativeName("th"));
        equal("pt-BR",LanguagePrefs.normalize(" PT_br "));
        equal("zh-Hant",LanguagePrefs.normalize("ZH_hant"));
        for(String invalid:new String[]{null,"","ja","en-US","pt-PT","0","../../en"}){
            if(LanguagePrefs.isValid(invalid))throw new AssertionError("Accepted invalid canonical choice");
            equal("system",LanguagePrefs.normalize(invalid));
        }
        if(LanguagePrefs.isValid("PT_br")||LanguagePrefs.isValid("EN"))throw new AssertionError("Backups require canonical codes");
        for(String[] pair:new String[][]{{"de-AT","de"},{"en-GB","en"},{"es-MX","es"},{"fr-CA","fr"},
                {"pt-PT","pt-BR"},{"pt-BR","pt-BR"},{"ru-RU","ru"},{"it-IT","it"},
                {"zh-CN","zh-Hant"},{"zh-Hant-TW","zh-Hant"},{"zh-Hans-SG","zh-Hant"},
                {"nl-BE","nl"},{"th-TH","th"},{"ko-KR","ko"},{"ja-JP","en"},{"ar-EG","en"}})
            equal(pair[1],LanguagePrefs.resolve("system",Locale.forLanguageTag(pair[0])));
        equal("en",LanguagePrefs.resolve("system",null));
        equal("en",LanguagePrefs.resolve("system",Locale.ROOT));
        equal("pt-BR",LanguagePrefs.resolve("invalid",Locale.forLanguageTag("pt-PT")));
        if(!before.equals(Locale.getDefault()))throw new AssertionError("Process Locale changed");
        System.out.println("PASS PGS languages: canonical choices, native labels, normalization, system matching and Locale isolation");
    }
}
