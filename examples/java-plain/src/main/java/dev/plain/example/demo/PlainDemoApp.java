package dev.plain.example.demo;

import dev.plain.example.login.LoginApp;

import java.util.Map;
import java.util.Scanner;

/**
 * Zero-framework quick-start demo: boots the login app over the
 * fire-after-commit engine's in-memory FactStore and drives the four
 * canonical scenarios from the console.
 *
 * <pre>
 *   mvn -pl java-plain test
 *   mvn -pl java-plain -am exec:java -Dexec.mainClass=dev.plain.example.demo.PlainDemoApp
 * </pre>
 */
public final class PlainDemoApp {

    private PlainDemoApp() {
    }

    public static void main(String[] args) {
        LoginApp app = LoginApp.create();
        System.out.println("java-plain — CLAD fire-after-commit engine, plain Java quick-start");
        System.out.println("Scenario keys: success | wrong-password | unknown-user | lockout | seed | quit");
        Scanner in = new Scanner(System.in);
        while (true) {
            System.out.print("> ");
            if (!in.hasNextLine()) {
                break;
            }
            String line = in.nextLine().trim();
            switch (line) {
                case "quit", "" -> { in.close(); return; }
                case "seed" -> {
                    app.seedUser("alice", "wonderland");
                    System.out.println("seeded user alice / wonderland");
                }
                case "success" -> {
                    app.seedUser("alice", "wonderland");
                    print(app.login("alice", "wonderland"));
                }
                case "wrong-password" -> {
                    app.seedUser("alice", "wonderland");
                    print(app.login("alice", "dead MQ"));
                }
                case "unknown-user" -> print(app.login("nobody", "test"));
                case "lockout" -> {
                    app.seedUser("eve", "snooping");
                    for (int i = 0; i < 5; i++) {
                        app.login("eve", "incorrect");
                    }
                    print(app.login("eve", "incorrect"));
                }
                default -> System.out.println("unknown key: " + line);
            }
        }
    }

    private static void print(Map<String, Object> response) {
        System.out.println(response);
    }
}
