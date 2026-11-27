package dev.pgs;

/** Ordered, unique catch-berry choices; no inventory data is persisted in the policy. */
public final class BerryPriority {
    private BerryPriority() {}
    public static boolean validId(int id) { return id==701||id==703||id==705||id==706||id==708; }
    /** Only historical user choices used 707 for Silver Pinap; real inventory IDs are never remapped. */
    public static int migrateLegacyId(int id) { return id==707?708:id; }
    public static String migrateLegacy(String value) {
        int[] ids=parse(value,true);
        StringBuilder saved=new StringBuilder();
        for(int id:ids){if(saved.length()>0)saved.append(',');saved.append(id);}
        return saved.toString();
    }
    public static int[] parse(String value) {
        return parse(value,false);
    }
    private static int[] parse(String value,boolean legacy) {
        if(value==null||value.length()>11)throw new IllegalArgumentException("Invalid berry priorities");
        if(value.isEmpty())return new int[0];
        String[] parts=value.split(",",-1);
        if(parts.length>3)throw new IllegalArgumentException("Too many berry priorities");
        int[] ids=new int[parts.length];
        for(int i=0;i<parts.length;i++){
            if(!parts[i].matches("[0-9]{3}"))throw new IllegalArgumentException("Invalid berry");
            ids[i]=Integer.parseInt(parts[i]);
            if(legacy)ids[i]=migrateLegacyId(ids[i]);
            if(!validId(ids[i]))throw new IllegalArgumentException("Invalid berry");
            for(int j=0;j<i;j++)if(ids[j]==ids[i])throw new IllegalArgumentException("Duplicate berry");
        }
        return ids;
    }
    public static String select(String current,int id) {
        if(id==0)return "";
        if(!validId(id))throw new IllegalArgumentException("Invalid berry");
        int[] ids=parse(current);
        if(ids.length==3)return String.valueOf(id);
        for(int chosen:ids)if(chosen==id)return current;
        return current.isEmpty()?String.valueOf(id):current+","+id;
    }
}
