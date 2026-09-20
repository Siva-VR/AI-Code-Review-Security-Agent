public class VulnerableSecurity {
    public void runQuery(String name, String table) {
        String password = "admin123";
        String api_key = "ABC-123-SECRET";
        String query = "SELECT * FROM " + table + " WHERE name = '" + name + "'";
        System.out.println(query + password + api_key);
        Runtime.getRuntime().exec("cmd /c dir " + name);
    }
}
