package dev.pgs;

import android.util.AtomicFile;
import java.io.*;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.Locale;
import java.util.Properties;

/** Separate JVMs and account destinations exercise global persistence and explicit backup imports. */
public final class ControlLanguageTest {
    private static void require(boolean yes,String message){if(!yes)throw new AssertionError(message);}
    private static Properties read(File file)throws IOException{
        Properties result=new Properties();try(FileInputStream in=new FileInputStream(file)){result.load(in);}return result;
    }
    private static void write(File file,Properties values)throws IOException{
        try(FileOutputStream out=new FileOutputStream(file)){values.store(out,"fixture");}
    }
    public static void main(String[] args)throws Exception{
        String phase=args[0];File root=new File(args[1]);root.mkdirs();
        File global=new File(root,"pgs-language-v1.properties");
        File profile=new File(root,"profile-"+(phase.equals("save")?"first":"second"));profile.mkdirs();
        AccountProfiles.directory=profile;
        File accountFile=new File(profile,"pgrazor-settings-v1.properties");
        Properties account=new Properties();account.setProperty(LanguagePrefs.KEY,"de");account.setProperty("darkTheme","false");
        write(accountFile,account); // A profile-local value must never override the global choice.
        if(phase.equals("invalid")){
            Properties invalid=new Properties();invalid.setProperty(LanguagePrefs.KEY,"not-a-language");write(global,invalid);
        }else if(phase.equals("malformed")){
            Files.write(global.toPath(),"pgsLanguage=\\uNOTHEX\n".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
        Locale processLocale=Locale.getDefault();
        android.app.Application app=new android.app.Application(){public File getFilesDir(){return root;}};
        Method load=Control.class.getDeclaredMethod("loadSettings",android.app.Application.class);load.setAccessible(true);load.invoke(null,app);
        require(!Control.darkTheme(),"Account fixture was not loaded");
        if(phase.equals("invalid")||phase.equals("malformed")){
            require(Control.pgsLanguage().equals("system"),"Corrupt global choice did not follow System");
            require(Control.exportSettings().getProperty(LanguagePrefs.KEY).equals("system"),"Fallback not exported canonically");
        }else if(phase.equals("save")){
            require(Control.pgsLanguage().equals("system"),"Old installation must default to System");
            Control.importSettings(app,new Properties(),9.3);
            require(Control.pgsLanguage().equals("system"),"Old backup changed the default");
            require(Control.setPgsLanguage("pt-BR"),"Valid choice was not saved");
            require(Control.pgsLanguage().equals("pt-BR"),"Pending restart choice not exposed to selector");
            require(read(global).getProperty(LanguagePrefs.KEY).equals("pt-BR"),"Language was not durably saved");
            require(!read(accountFile).containsKey(LanguagePrefs.KEY),"Language leaked into account settings");
            File copied=new File(root,"copied-account.properties");Control.retargetSettings(copied);
            require(!read(copied).containsKey(LanguagePrefs.KEY),"Retargeting accounts copied global language");
            require(Control.setPgsLanguage("ko")&&Control.setPgsLanguage("pt-BR"),"Choice after account retarget failed");
            require(read(global).getProperty(LanguagePrefs.KEY).equals("pt-BR")&&!read(copied).containsKey(LanguagePrefs.KEY),
                "Account retarget moved the global destination");
        }else{
            require(Control.pgsLanguage().equals("pt-BR"),"Cold start on another account lost global choice");
            Properties oldDefaults=new Properties();oldDefaults.setProperty(LanguagePrefs.KEY,"de");
            Control.importSettings(app,new Properties(oldDefaults),9.3);
            require(Control.pgsLanguage().equals("pt-BR"),"Old backup without an explicit key changed global language");
            Properties incoming=new Properties();incoming.setProperty(LanguagePrefs.KEY,"zh-Hant");incoming.setProperty("darkTheme","true");
            Control.importSettings(app,incoming,9.3);
            require(Control.pgsLanguage().equals("zh-Hant")&&Control.darkTheme(),"Explicit language import failed");
            require(read(global).getProperty(LanguagePrefs.KEY).equals("zh-Hant"),"Imported language was not durable");
            require(!read(accountFile).containsKey(LanguagePrefs.KEY),"Import copied global language into a profile");
            require(Control.exportSettings().getProperty(LanguagePrefs.KEY).equals("zh-Hant"),"Export lost global language");
            require(incoming.getProperty(LanguagePrefs.KEY).equals("zh-Hant"),"Import mutated caller properties");
            for(String invalid:new String[]{null,"","ja","PT_br","en-US","../../en"})
                require(!Control.setPgsLanguage(invalid)&&Control.pgsLanguage().equals("zh-Hant"),"Invalid selector choice replaced saved choice");
            Properties before=read(accountFile);byte[] globalBefore=Files.readAllBytes(global.toPath());
            for(Object invalid:new Object[]{"ja","PT_br","",7}){
                Properties bad=new Properties();bad.put(LanguagePrefs.KEY,invalid);bad.setProperty("darkTheme","false");
                try{Control.importSettings(app,bad,9.3);throw new AssertionError("Invalid language import accepted");}catch(IOException expected){}
                require(Control.pgsLanguage().equals("zh-Hant")&&Control.darkTheme(),"Invalid import changed live settings");
                require(before.equals(read(accountFile))&&Arrays.equals(globalBefore,Files.readAllBytes(global.toPath())),"Invalid import wrote settings");
            }
            Field destination=Control.class.getDeclaredField("pgsLanguageFile");destination.setAccessible(true);Object original=destination.get(null);
            destination.set(null,new AtomicFile(global){
                @Override public FileOutputStream startWrite()throws IOException{throw new IOException("disk unavailable");}
            });
            try{
                require(!Control.setPgsLanguage("fr")&&Control.pgsLanguage().equals("zh-Hant"),"Failed save changed selection");
                Properties failed=new Properties();failed.setProperty(LanguagePrefs.KEY,"fr");failed.setProperty("darkTheme","false");
                try{Control.importSettings(app,failed,9.3);throw new AssertionError("Failed global import reported success");}catch(IOException expected){}
                require(Control.pgsLanguage().equals("zh-Hant")&&Control.darkTheme(),"Failed import changed live choices");
                require(before.equals(read(accountFile)),"Failed global import did not roll back account settings");
                require(Arrays.equals(globalBefore,Files.readAllBytes(global.toPath())),"Failed save replaced global preference");
            }finally{destination.set(null,original);}
            load.invoke(null,app);
            require(Control.pgsLanguage().equals("zh-Hant"),"Settings reload reset the pending language choice");
        }
        require(processLocale.equals(Locale.getDefault()),"Language preference changed the process/game Locale");
        Control.flushSettings(5000);
        System.out.println("PASS PGS language "+phase+": global persistence, backup migration, validation and profile isolation");
    }
}
