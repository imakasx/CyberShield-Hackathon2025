import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public class SimpleCSV {
    // random platforms
    private static final List<String> PLATFORMS = Arrays.asList(
            "Twitter/X", "Facebook", "Instagram", "YouTube", "Telegram",
            "Reddit", "Quora", "Koo", "LinkedIn", "WhatsApp"
    );

    // favour India
    private static final List<String> PRO_TEXTS = Arrays.asList(
            "भारत के वैज्ञानिकों पर गर्व है।",
            "India’s startups are growing fast.",
            "हमारी एकता ही हमारी ताकत है।",
            "ISRO की success ने दुनिया को inspire किया।",
            "Make in India बढ़ा रहा है manufacturing."
    );

    // against India
    private static final List<String> AGAINST_TEXTS = Arrays.asList(
            "India को गलत तरीके से दिखाया जा रहा है।",
            "Misleading claims about Indian policies.",
            "भारत के खिलाफ biased narrative है।",
            "Unverified allegations used to criticise India.",
            "India को unfair तरीके से judge किया गया।"
    );

    public static void main(String[] args) {
        int rows = 50; // kitni rows
        String file = "file.csv";

        try {
            generate(file, rows);
            System.out.println("CSV created: " + Paths.get(file).toAbsolutePath());
        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
        }
    }

    private static void generate(String file, int rows) throws IOException {
        Random rnd = new Random();

        try (BufferedWriter bw = Files.newBufferedWriter(
                Paths.get(file), StandardCharsets.UTF_8,
                StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {

            // header
            bw.write("id,platform,text");
            bw.newLine();

            for (int id = 1; id <= rows; id++) {
                String platform = PLATFORMS.get(rnd.nextInt(PLATFORMS.size()));
                boolean pro = rnd.nextBoolean();
                String text = pro
                        ? PRO_TEXTS.get(rnd.nextInt(PRO_TEXTS.size()))
                        : AGAINST_TEXTS.get(rnd.nextInt(AGAINST_TEXTS.size()));

                // write row
                bw.write(id + "," + csv(platform) + "," + csv(text));
                bw.newLine();
            }
        }
    }

    // csv safe
    private static String csv(String s) {
        return "\"" + s.replace("\"", "\"\"") + "\"";
    }
}
