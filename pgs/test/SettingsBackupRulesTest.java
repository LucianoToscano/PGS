import dev.pgs.SettingsBackupRules;
import dev.pgs.BerryPriority;
import dev.pgs.MapTapSequence;
import dev.pgs.LanguagePrefs;
import org.json.*;

public class SettingsBackupRulesTest {
    private static JSONObject valid()throws Exception{
        return new JSONObject().put("format","PGS settings").put("version",1).put("speedKmh",9.3)
            .put("settings",new JSONObject().put("autoDismiss","true").put("transferProtect","63"))
            .put("preferences",new JSONObject().put("pgs-overlays",new JSONObject().put("vgp.fx",0.8)));
    }
    private static void rejects(JSONObject value)throws Exception{
        try{SettingsBackupRules.validate(value);}catch(JSONException expected){return;}throw new AssertionError("Accepted invalid backup");
    }
    public static void main(String[] args)throws Exception{
        SettingsBackupRules.validate(valid());
        SettingsBackupRules.validate(valid().put("format","PGS settings"));
        JSONObject legacy=valid();
        JSONObject normalized=SettingsBackupRules.canonicalPreferences(legacy);
        if(!normalized.has("pgs-overlays")||!legacy.getJSONObject("preferences").has("pgs-overlays")||normalized.has("pgs-overlays"))
            throw new AssertionError("Legacy backup scope normalization failed");
        JSONObject modern=valid().put("format","PGS settings").put("version",2).put("preferences",
            new JSONObject().put("pgs-overlays",new JSONObject().put("vgp.fx",0.8)));
        SettingsBackupRules.validate(modern);
        if(!SettingsBackupRules.canonicalPreferences(modern).has("pgs-overlays"))throw new AssertionError("PGS scope lost");
        rejects(valid().put("format","PGS settings").put("version",2));
        rejects(valid().put("version",2));
        rejects(valid().put("format","PGS settings").put("preferences",new JSONObject().put("pgs-overlays",new JSONObject())));
        rejects(new JSONObject(modern.toString()).put("format","PGS settings"));
        JSONObject mixed=new JSONObject(modern.toString());
        mixed.getJSONObject("preferences").put("pgs-overlays",new JSONObject());
        rejects(mixed);
        JSONObject badModern=new JSONObject(modern.toString());
        badModern.getJSONObject("preferences").getJSONObject("pgs-overlays").put("vgp.fx",1.2);
        rejects(badModern);
        rejects(valid().put("format","unrecognized"));
        // Old exported backups continue to import without changing preferences or losing data.
        JSONObject oldLanguage=valid();SettingsBackupRules.validate(oldLanguage);
        if(oldLanguage.getJSONObject("settings").has(LanguagePrefs.KEY))throw new AssertionError("Old backup was mutated");
        for(String code:LanguagePrefs.codes()){
            JSONObject language=valid();language.getJSONObject("settings").put(LanguagePrefs.KEY,code);
            SettingsBackupRules.validate(language);
            if(!language.getJSONObject("settings").getString(LanguagePrefs.KEY).equals(code))throw new AssertionError("Language validation changed selection");
        }
        for(Object invalid:new Object[]{"","ja","pt","pt_br","PT-BR","zh-CN","en-US"," system",7,true,JSONObject.NULL}){
            JSONObject language=valid();language.getJSONObject("settings").put(LanguagePrefs.KEY,invalid);rejects(language);
        }
        JSONObject protect=valid();protect.getJSONObject("settings").put("transferProtect","255").put("transferProtectSplit","1");
        SettingsBackupRules.validate(protect);
        protect.getJSONObject("settings").put("transferProtect","2047").put("transferProtectShadow","1").put("transferProtectMax","1");
        SettingsBackupRules.validate(protect);
        protect.getJSONObject("settings").put("transferProtect","2048");rejects(protect);
        protect.getJSONObject("settings").put("transferProtect","2047").put("transferProtectShadow","2");rejects(protect);
        protect.getJSONObject("settings").put("transferProtectShadow","1").put("transferProtectMax","2");rejects(protect);
        JSONObject autoThrow=valid();autoThrow.getJSONObject("settings").put("autoThrow","true").put("autoThrowOnMap","true");
        SettingsBackupRules.validate(autoThrow);
        autoThrow.getJSONObject("settings").put("autoThrowOnMap","false");SettingsBackupRules.validate(autoThrow);
        autoThrow.getJSONObject("settings").put("autoThrowOnMap","yes");rejects(autoThrow);

        JSONObject raids=valid();raids.getJSONObject("settings").put("autoRaidTierMask","127").put("autoRaidBosses","150,384")
            .put("autoRaidMaxRaids","5").put("autoRaidMinPlayers","3").put("autoRaidWaitSeconds","60")
            .put("autoRaidFreePass","true").put("autoRaidPremiumPass","false")
            .put("autoRaidRazzBerry","true").put("autoRaidGoldenRazzBerry","false").put("autoRaidMaxDistanceKm","5");SettingsBackupRules.validate(raids);
        raids.getJSONObject("settings").put("autoRaidRazzBerry","false").put("autoRaidGoldenRazzBerry","true");SettingsBackupRules.validate(raids);
        for(String[] invalid:new String[][]{{"autoRaidTierMask","128"},{"autoRaidBosses","0"},{"autoRaidMaxRaids","0"},
                {"autoRaidMinPlayers","21"},{"autoRaidMaxDistanceKm","3"},{"autoRaidWaitSeconds","121"},{"autoRaidPremiumPass","yes"},
                {"autoRaidRazzBerry","yes"},{"autoRaidGoldenRazzBerry","701"},{"autoRaidRunning","true"}}){
            JSONObject badRaid=valid();badRaid.getJSONObject("settings").put(invalid[0],invalid[1]);rejects(badRaid);
        }
        JSONObject buddyOrder=valid();buddyOrder.getJSONObject("settings").put("buddyEmotionBerries","708,703,701");SettingsBackupRules.validate(buddyOrder);
        for(String bad:new String[]{"703,703","707","703,","1201"}){buddyOrder.getJSONObject("settings").put("buddyEmotionBerries",bad);rejects(buddyOrder);}
        buddyOrder.getJSONObject("settings").put("buddyEmotionBerries","");SettingsBackupRules.validate(buddyOrder);
        MapTapSequence taps=new MapTapSequence();
        if(taps.doubleTap(40,-70,1000,1,300)||!taps.doubleTap(40.00001,-70,1200,1,300)||taps.doubleTap(40,-70,1300,1,300))throw new AssertionError("Tap pair/triple handling");
        if(taps.doubleTap(41,-70,1400,1,300)||taps.doubleTap(41,-70,1500,2,300)||taps.doubleTap(41,-70,1900,2,300))throw new AssertionError("Distant, expired, or old-generation tap paired");
        JSONObject tapSetting=valid();tapSetting.getJSONObject("settings").put("mapTap","3");SettingsBackupRules.validate(tapSetting);
        tapSetting.getJSONObject("settings").put("mapTap","4");rejects(tapSetting);
        for(int scale:new int[]{100,75,50,25}){JSONObject scaled=valid();scaled.getJSONObject("settings").put("uiScalePercent",String.valueOf(scale));SettingsBackupRules.validate(scaled);}
        for(String scale:new String[]{"0","24","101","50.5","bad"}){JSONObject scaled=valid();scaled.getJSONObject("settings").put("uiScalePercent",scale);rejects(scaled);}
        String choices="";
        choices=BerryPriority.select(choices,708);choices=BerryPriority.select(choices,705);choices=BerryPriority.select(choices,701);
        if(!choices.equals("708,705,701"))throw new AssertionError("Selection order lost");
        if(!BerryPriority.select(choices,706).equals("706"))throw new AssertionError("Fourth choice must reset");
        if(!BerryPriority.select(choices,0).isEmpty())throw new AssertionError("Off must clear all");
        if(!BerryPriority.select("708,705",708).equals("708,705"))throw new AssertionError("Duplicate priority");
        if(BerryPriority.validId(707)||!BerryPriority.validId(708))throw new AssertionError("Silver Pinap must use its game item ID");
        try{BerryPriority.select("705",707);throw new AssertionError("New choice accepted legacy berry ID");}catch(IllegalArgumentException expected){}
        try{BerryPriority.parse("707");throw new AssertionError("Runtime parser accepted legacy berry ID");}catch(IllegalArgumentException expected){}
        if(!BerryPriority.migrateLegacy("707,705,701").equals(choices)||!BerryPriority.migrateLegacy(choices).equals(choices)||!BerryPriority.migrateLegacy("").isEmpty())
            throw new AssertionError("Legacy berry migration must preserve order, be idempotent, and keep Off");
        JSONObject berries=valid();berries.getJSONObject("settings").put("berryPriority",choices);SettingsBackupRules.validate(berries);
        berries.getJSONObject("settings").put("berryPriority","707,705,701");SettingsBackupRules.validate(berries);
        if(!berries.getJSONObject("settings").getString("berryPriority").equals("707,705,701"))throw new AssertionError("Backup validation must not mutate input");
        berries.getJSONObject("settings").put("berryPriority","");SettingsBackupRules.validate(berries);
        for(String bad:new String[]{"701,701","707,707","707,708","708,707","701,703,705,706","702","701,","701, 703","0"}){berries.getJSONObject("settings").put("berryPriority",bad);rejects(berries);}
        for(String key:new String[]{"buddyBerry","autoBerry"}){
            for(String id:new String[]{"0","701","703","705","706","707","708"}){JSONObject oldBerry=valid();oldBerry.getJSONObject("settings").put(key,id);SettingsBackupRules.validate(oldBerry);}
            for(String id:new String[]{"702","704","709","-708","708.0"}){JSONObject badBerry=valid();badBerry.getJSONObject("settings").put(key,id);rejects(badBerry);}
        }
        rejects(valid().put("version",1.5));rejects(valid().put("speedKmh",99));
        JSONObject v=valid();v.getJSONObject("settings").put("vgpEnabled","true");rejects(v);
        for(String mask:new String[]{"0","8191","8192","16383"}){v=valid();v.getJSONObject("settings").put("quickMenuHidden",mask);SettingsBackupRules.validate(v);}
        for(String mask:new String[]{"-1","16384","8192.5"}){v=valid();v.getJSONObject("settings").put("quickMenuHidden",mask);rejects(v);}
        v=valid();v.getJSONObject("preferences").put("pgs-livefeed-session",new JSONObject().put("token","secret"));rejects(v);
        v=valid();v.getJSONObject("settings").put("itemRules","1:100001;");rejects(v);
        v=valid();v.getJSONObject("settings").put("idleWalking","true");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("idleWalking","maybe");rejects(v);
        v=valid();v.getJSONObject("settings").put("localTimeOverlay","true");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("localTimeOverlay","maybe");rejects(v);
        v=valid();v.getJSONObject("preferences").put("pgs-overlays",new JSONObject().put("local-time.fx",0.3).put("local-time.fy",0.6));SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("preferences").put("pgs-overlays",new JSONObject().put("local-time.fx",1.2));rejects(v);
        v=valid();v.getJSONObject("settings").put("locationSpoofing","false");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("locationSpoofing","invalid");rejects(v);
        v=valid();v.getJSONObject("settings").put("ivCatch","false").put("ivOwned","true");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("ivOwned","maybe");rejects(v);
        v=valid();v.getJSONObject("settings").put("storageIv","3");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("storageIv","4");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("storageIv","5");rejects(v);
        v=valid();v.getJSONObject("settings").put("storageIvFormat","2");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("storageIvFormat","9");rejects(v);
        v=valid();v.getJSONObject("settings").put("ivCatchFormat","3");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("ivOwnedFormat","5");rejects(v);
        v=valid();v.getJSONObject("settings").put("catchChance","false").put("autoBall","true").put("autoBallTarget","85");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("autoBallTarget","100");rejects(v);
        v=valid();v.getJSONObject("settings").put("pvpKeepLeagues","7").put("pvpGreatRank","100").put("pvpUltraRank","10").put("pvpMasterRank","25");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("pvpKeepLeagues","8");rejects(v);
        v=valid();v.getJSONObject("settings").put("pvpUltraRank","0");rejects(v);
        v=valid();v.getJSONObject("settings").put("autoBall","yes");rejects(v);
        v=valid();v.getJSONObject("preferences").put("pgs-overlays",new JSONObject().put("vgp.fx",1.2));rejects(v);
        v=valid();v.getJSONObject("settings").put("gymAutomationOverlay","false");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("gymAutomationOverlay","maybe");rejects(v);
        v=valid();v.getJSONObject("settings").put("gymAutomationSpin","true");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("gymAutomationSpin","false");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("gymAutomationSpin","1");rejects(v);
        v=valid();v.getJSONObject("settings").put("gymRepeatEnabled","true");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("gymRepeatEnabled","false");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("gymRepeatEnabled","maybe");rejects(v);
        v=valid();v.getJSONObject("settings").put("smartCatchSpinGyms","true");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("smartCatchSpinGyms","false");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("smartCatchSpinGyms","1");rejects(v);
        v=valid();v.getJSONObject("settings").put("smartCatchAutoBall","true").put("smartCatchAutoBallTarget","90");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("smartCatchAutoBall","1");rejects(v);
        v=valid();v.getJSONObject("settings").put("smartCatchAutoBallTarget","0");rejects(v);
        v=valid();v.getJSONObject("settings").put("smartCatchAutoBallTarget","100");rejects(v);
        v=valid();v.getJSONObject("preferences").put("pgs-overlays",new JSONObject().put("gym-feed.fx",0.4).put("gym-feed.fy",0.6));SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("preferences").put("pgs-overlays",new JSONObject().put("gym-feed.fx",1.1));rejects(v);
        // Transfer keep list and Keep All / overlay settings.
        v=valid();v.getJSONObject("settings").put("transferKeepAll","true").put("transferOverlay","false").put("transferKeepSpecies","1,4,25,2000");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies","");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("shundoSpecies","1,129,2000");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("shundoSpecies","");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("shundoSpecies","129,129");rejects(v);           // duplicate dex id
        v=valid();v.getJSONObject("settings").put("shundoGap","60");SettingsBackupRules.validate(v);
        for(String ok:new String[]{"30","60","180","300","600"}){v=valid();v.getJSONObject("settings").put("shundoLiveInterval",ok);SettingsBackupRules.validate(v);}
        v=valid();v.getJSONObject("settings").put("shinyScan","true").put("shinyScanSpeed","2").put("shinyScanSpecies","25,129")
            .put("shinyScanDailyLimit","5000").put("encounterCounter","false").put("encounterOverlay","true");SettingsBackupRules.validate(v);
        for(String[] bad:new String[][]{{"shinyScan","yes"},{"shinyScanSpeed","3"},{"shinyScanSpecies","0"},{"shinyScanDailyLimit","123"},{"shinyScanDay","20261115"},{"encounterOverlay","yes"}}){
            v=valid();v.getJSONObject("settings").put(bad[0],bad[1]);rejects(v);}
        v=valid();v.getJSONObject("settings").put("shundoGap","45");rejects(v);                    // not an offered gap
        for(String bad:new String[]{"0","15","45","900","","5m"}){v=valid();v.getJSONObject("settings").put("shundoLiveInterval",bad);rejects(v);}
        {StringBuilder many=new StringBuilder();for(int i=1;i<=501;i++){if(i>1)many.append(',');many.append(i);}
         v=valid();v.getJSONObject("settings").put("shundoSpecies",many.toString());rejects(v);}   // over 500 species
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies","1,4,2001");rejects(v);   // out of range (>2000)
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies","0");rejects(v);           // zero is not positive
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies","1,4,abc");rejects(v);      // non-numeric token
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies","1,1");rejects(v);          // duplicate dex id
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies","1,,4");rejects(v);         // empty token
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies","01");rejects(v);           // leading zero
        v=valid();v.getJSONObject("settings").put("transferKeepSpecies",new String(new char[11000]).replace('\0','1'));rejects(v); // over length bound
        v=valid();v.getJSONObject("settings").put("transferKeepAll","maybe");rejects(v);
        v=valid();v.getJSONObject("settings").put("transferOverlay","yes");rejects(v);
        // Evolve before transferring: enable flag, mode (0/1), stages (1/2) and an independent species list.
        v=valid();v.getJSONObject("settings").put("evolveTransferEnabled","true").put("evolveTransferMode","1").put("evolveTransferStages","2").put("evolveTransferSpecies","1,4,25");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("evolveTransferEnabled","false").put("evolveTransferMode","0").put("evolveTransferStages","1").put("evolveTransferSpecies","");SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("settings").put("evolveTransferEnabled","maybe");rejects(v);
        v=valid();v.getJSONObject("settings").put("evolveTransferMode","2");rejects(v);            // only 0 or 1
        v=valid();v.getJSONObject("settings").put("evolveTransferStages","0");rejects(v);           // only 1 or 2
        v=valid();v.getJSONObject("settings").put("evolveTransferStages","3");rejects(v);
        v=valid();v.getJSONObject("settings").put("evolveTransferSpecies","1,1");rejects(v);         // duplicate dex id
        v=valid();v.getJSONObject("settings").put("evolveTransferSpecies","2001");rejects(v);        // out of range (>2000)
        v=valid();v.getJSONObject("preferences").put("pgs-overlays",new JSONObject().put("transfer.fx",0.5).put("transfer.fy",0.25));SettingsBackupRules.validate(v);
        v=valid();v.getJSONObject("preferences").put("pgs-overlays",new JSONObject().put("transfer.fx",1.5));rejects(v);
        for(int r:new int[]{0,1,2,3}){v=valid();v.getJSONObject("preferences").put("pgs-livefeed",new JSONObject().put("radius",r));SettingsBackupRules.validate(v);}
        for(Object bad:new Object[]{-1,4,1.5,"2",true}){v=valid();v.getJSONObject("preferences").put("pgs-livefeed",new JSONObject().put("radius",bad));rejects(v);}
        String places="[{\"id\":\"a\",\"name\":\"Home\",\"latitude\":40,\"longitude\":-70}]";
        v=valid();v.getJSONObject("preferences").put("pgs-saved-places-v1",new JSONObject().put("places",places));SettingsBackupRules.validate(v);
        v.getJSONObject("preferences").getJSONObject("pgs-saved-places-v1").put("places",places.replace("40","400"));rejects(v);
        System.out.println("PASS settings backup: valid settings/favorites, schema, credential and VGP exclusion, bounds, IV display booleans, transfer keep list/Keep All/overlay validation, evolve-before-transfer enable/mode/stages/species validation and preference types");
    }
}
