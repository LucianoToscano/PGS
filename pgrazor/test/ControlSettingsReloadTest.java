package dev.pgrazor;

import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/** A failed pending save must never make reload replace live choices with an older disk snapshot. */
public final class ControlSettingsReloadTest {
    public static void main(String[] args) throws Exception {
        android.app.Application app=new android.app.Application() {
            public java.io.File getFilesDir(){return new java.io.File(args[0]);}
        };
        Method load=Control.class.getDeclaredMethod("loadSettings",android.app.Application.class);
        if(Control.gymRepeatEnabled())throw new AssertionError("Gym repeat should default off");
        if(Control.localTimeOverlay())throw new AssertionError("Local clock should default off");
        load.setAccessible(true); load.invoke(null,app);
        Control.setGymRepeatEnabled(true);
        Control.setLocalTimeOverlay(true);
        if(!"true".equals(Control.exportSettings().getProperty("localTimeOverlay")))
            throw new AssertionError("Export missed local clock toggle");
        if(!"true".equals(Control.exportSettings().getProperty("gymRepeatEnabled")))
            throw new AssertionError("Export missed gym repeat toggle");
        Control.setBattleOptions(111); Control.setBattleOptions(981);
        if(!"981".equals(Control.exportSettings().getProperty("battleOptions")))
            throw new AssertionError("Export missed latest queued choice");
        Control.setAutoBerry(705); Control.setBattleOptions(2);
        java.util.Properties incoming=new java.util.Properties();
        incoming.setProperty("localTimeOverlay","false");
        incoming.setProperty("idleWalking","false"); incoming.setProperty("battleOptions","5"); incoming.setProperty("autoBerry","701"); incoming.setProperty("gymRepeatEnabled","false");
        Control.importSettings(app,incoming,9.3); Control.flushSettings(5000);
        if(Control.idleWalking())throw new AssertionError("Idle walking import did not apply false");
        if(Control.gymRepeatEnabled())throw new AssertionError("Gym repeat import did not apply false");
        if(Control.localTimeOverlay())throw new AssertionError("Local clock import did not apply false");
        if(Control.battleOptions()!=5 || Control.autoBerry()!=701 || Control.vgpEnabled())
            throw new AssertionError("Import ordering, legacy berry migration or VGP OFF changed");
        if(!"5".equals(Control.exportSettings().getProperty("battleOptions")))
            throw new AssertionError("A queued snapshot overwrote imported choices");
        // Only saved legacy choices used 707 for Silver Pinap; live inventory IDs retain their meaning.
        java.util.Properties oldSilver=new java.util.Properties();
        oldSilver.setProperty("autoBerry","707");oldSilver.setProperty("buddyBerry","707");oldSilver.setProperty("encounterBerry","true");
        Control.importSettings(app,oldSilver,9.3);Control.flushSettings(5000);
        if(Control.autoBerry()!=708||Control.buddyBerry()!=708||!Control.berryPriority().equals("708")||Control.vgpEnabled()||Control.buddyAllowed())
            throw new AssertionError("Legacy single Silver Pinap migration changed its meaning or bypassed readiness");
        java.util.Properties migrated=new java.util.Properties();
        try(java.io.FileInputStream in=new java.io.FileInputStream(new java.io.File(args[0],"pgrazor-settings-v1.properties"))){migrated.load(in);}
        if(!"708".equals(migrated.getProperty("berryPriority"))||!"708".equals(migrated.getProperty("buddyBerry"))||migrated.containsKey("autoBerry"))
            throw new AssertionError("Legacy migration was not persisted canonically");
        Control.selectBerryPriority(705);
        Control.setItemCatalog("707|Golden Nanab Berry|99\n708|Silver Pinap Berry|0\n705|Pinap Berry|2");
        if(Control.autoBerry()!=705||Control.berryCount(707)!=99||Control.berryCount(708)!=0)
            throw new AssertionError("Unstocked Silver Pinap must fall back without relabeling real inventory 707");
        Control.setItemCatalog("707|Golden Nanab Berry|99\n708|Silver Pinap Berry|4\n705|Pinap Berry|2");
        if(Control.autoBerry()!=708)throw new AssertionError("Stocked Silver Pinap did not regain priority");
        Control.setAutoBerry(707);Control.selectBerryPriority(707);Control.setBuddyBerry(703);Control.setBuddyBerry(707);
        if(!Control.berryPriority().equals("708,705")||Control.buddyBerry()!=703)
            throw new AssertionError("Runtime setters must reject historical item IDs");
        oldSilver.remove("autoBerry");oldSilver.setProperty("berryPriority","707,705,701");oldSilver.setProperty("encounterBerry","false");
        Control.importSettings(app,oldSilver,9.3);Control.flushSettings(5000);load.invoke(null,app);
        if(!Control.berryPriority().equals("708,705,701")||Control.buddyBerry()!=708||Control.encounterBerryEnabled()||Control.autoBerry()!=0||!Control.effectiveBerryPriority().isEmpty())
            throw new AssertionError("Ordered legacy migration lost order, persistence or the explicit disabled choice");
        migrated=Control.exportSettings();
        if(!"708,705,701".equals(migrated.getProperty("berryPriority"))||!"708".equals(migrated.getProperty("buddyBerry")))
            throw new AssertionError("Export reintroduced legacy berry IDs");
        oldSilver.setProperty("berryPriority","707,708");Control.importSettings(app,oldSilver,9.3);Control.flushSettings(5000);
        if(!Control.berryPriority().isEmpty())throw new AssertionError("Ambiguous duplicate legacy priorities must fail closed");
        // Evolve before transferring: a corrupt persisted mode must fail safe and disable the feature on reload.
        Control.setAutoTransferEnabled(true);
        Control.setEvolveTransferEnabled(true); Control.setEvolveTransferMode(1); Control.setEvolveTransferStages(2); Control.setEvolveTransferSpecies("1,4,25");
        if(!Control.evolveTransferEnabled()||Control.evolveTransferMode()!=1||Control.evolveTransferStages()!=2||!Control.evolveTransferSpecies().equals("1,4,25"))
            throw new AssertionError("Evolve-before-transfer choices not applied before import");
        java.util.Properties corruptEvolve=new java.util.Properties(); corruptEvolve.setProperty("evolveTransferMode","9");
        Control.importSettings(app,corruptEvolve,9.3); Control.flushSettings(5000);
        if(Control.autoTransferEnabled()||Control.evolveTransferEnabled()||Control.evolveTransferMode()!=0||Control.evolveTransferStages()!=2||!Control.evolveTransferSpecies().equals("1,4,25"))
            throw new AssertionError("Corrupt evolve-transfer mode did not fail safe to disabled on reload");
        // Backups from before costume had its own option: "event / costume" on keeps both, off keeps neither.
        java.util.Properties oldProtect=new java.util.Properties(); oldProtect.setProperty("transferProtect","127");
        Control.importSettings(app,oldProtect,9.3); Control.flushSettings(5000);
        // ...and backups from before Keep shadow Pokemon (bit 256) keep shadows.
        if(Control.transferProtect()!=2047)throw new AssertionError("Old event/costume choice did not keep costumes, shadows and Max Pokemon");
        oldProtect.setProperty("transferProtect","123");
        Control.importSettings(app,oldProtect,9.3); Control.flushSettings(5000);
        if(Control.transferProtect()!=(123|256|1536))throw new AssertionError("Old event/costume off turned costume keeping on");
        // A current backup keeps the two choices apart, and the choice survives a reload.
        oldProtect.setProperty("transferProtect","4"); oldProtect.setProperty("transferProtectSplit","1");
        Control.importSettings(app,oldProtect,9.3); Control.flushSettings(5000);
        if(Control.transferProtect()!=(4|256|1536))throw new AssertionError("Backup from before Keep shadow did not keep shadows");
        oldProtect.setProperty("transferProtectShadow","1");
        Control.importSettings(app,oldProtect,9.3); Control.flushSettings(5000);
        if(Control.transferProtect()!=(4|1536))throw new AssertionError("Backup from before Keep Dynamax/Gigantamax did not keep them");
        oldProtect.setProperty("transferProtectMax","1");
        Control.importSettings(app,oldProtect,9.3); Control.flushSettings(5000);
        load.invoke(null,app);
        if(Control.transferProtect()!=4)throw new AssertionError("Event-only protection was not preserved");
        Control.setDarkTheme(false); Control.flushSettings(5000);
        Field writer=Control.class.getDeclaredField("settingsWriter"); writer.setAccessible(true);
        Object original=writer.get(null);
        writer.set(null,new SettingsWriter(Runnable::run,p->{throw new IOException("disk unavailable");},e->{}));
        try {
            Control.setDarkTheme(true);
            load.invoke(null,app);
            if(!Control.darkTheme())throw new AssertionError("Failed save allowed stale settings reload");
        } finally { writer.set(null,original); }
        System.out.println("PASS: export/import ordering, migration, evolve-transfer corrupt-config fail-safe and failed-save reload isolation");
    }
}
