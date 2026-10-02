/*
 * Validate SysML v2 textual files with the OMG SysML v2 Pilot Implementation.
 *
 *   java -cp <jupyter-sysml-kernel-all.jar> tools/sysml/ValidateSysML.java <sysml.library/> <file.sysml>...
 *
 * Files are processed in the order given, in one session, so later files may
 * reference packages declared in earlier ones. Prints one line per issue and
 * exits 1 if any file has a syntax or semantic error (warnings do not fail).
 */
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import org.eclipse.xtext.validation.Issue;
import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.interactive.SysMLInteractiveResult;

public class ValidateSysML {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: ValidateSysML <sysml.library/> <file.sysml>...");
            System.exit(2);
        }
        String library = args[0].endsWith("/") ? args[0] : args[0] + "/";
        SysMLInteractive sysml = SysMLInteractive.getInstance();
        sysml.loadLibrary(library);

        int errors = 0, warnings = 0;
        for (int i = 1; i < args.length; i++) {
            String file = args[i];
            SysMLInteractiveResult result = sysml.process(Files.readString(Path.of(file)));
            if (result.getException() != null) {
                System.out.println(file + ": ERROR: " + result.formatException());
                errors++;
                continue;
            }
            errors += report(file, "ERROR", result.getSyntaxErrors());
            errors += report(file, "ERROR", result.getSemanticErrors());
            warnings += report(file, "WARNING", result.getWarnings());
            System.out.println(file + ": processed");
        }
        System.out.println((errors > 0 ? "FAIL" : "PASS") + ": " + errors + " error(s), " + warnings + " warning(s)");
        System.exit(errors > 0 ? 1 : 0);
    }

    private static int report(String file, String severity, List<Issue> issues) {
        for (Issue issue : issues) {
            System.out.println(file + ":" + issue.getLineNumber() + ":" + issue.getColumn()
                    + ": " + severity + ": " + issue.getMessage());
        }
        return issues.size();
    }
}
