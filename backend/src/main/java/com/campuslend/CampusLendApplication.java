package com.campuslend;

import com.campuslend.model.Item;
import com.campuslend.model.Student;
import com.campuslend.repository.ItemRepository;
import com.campuslend.repository.StudentRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.List;

@SpringBootApplication
public class CampusLendApplication {

    public static void main(String[] args) {
        SpringApplication.run(CampusLendApplication.class, args);
    }

    @Bean
    CommandLineRunner initDatabase(ItemRepository itemRepository,
                                  StudentRepository studentRepository,
                                  PasswordEncoder passwordEncoder) {
        return args -> {
            // 1. Seed demo student if none exists
            if (studentRepository.count() == 0) {
                Student demoStudent = new Student(
                        "SU-9824102",
                        "Alex J. Chen",
                        "alex.chen@stanford.edu",
                        passwordEncoder.encode("Stanford2026!"),
                        "Computer Science & Engineering",
                        "Junior"
                );
                studentRepository.save(demoStudent);
                System.out.println("✅ Preloaded demo student: alex.chen@stanford.edu");
            }

            // 2. Seed initial catalog items if empty
            if (itemRepository.count() == 0) {
                List<Item> initialCatalog = List.of(
                        new Item(
                                "item-1",
                                "TI-84 Plus CE Graphing Calculator",
                                "stationery",
                                "Calculators & Lab",
                                3.50,
                                20.00,
                                "Like New",
                                "Wilbur Hall • 0.2 mi",
                                "Stanford Campus",
                                "Sarah Lin",
                                "Sophomore • Applied Mathematics",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuBM8VSzPWz6gX7VI2wzCYRejzZ-cxNpuaEF-mrtYyc4P20zvX2frfHkS75qBmQ7sNSciIYrMNM5VK1ZMyXi3W8ShFLb7o-zZNhhGqJAdNUbM3Z-b77r5tSXgdPIB6dd4mzmgFolQkHmrepl88pZ7AKd6OFrAyTCVunaRI3SuyVpfaalf0FqpiFIZkBil0Rq-_pMRvPb1lpO70yIbtS2D1m0a7Z9-EWNDqXSpV3R7YzR",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuCwzEoEAOySUGjNOHtVUJfX4kzk2JoXBWr8O_2W6OlPBOBEyzFpdkwPF9maQ9UpdNsMNhfCUS2r3co300xpXSH1WgDkybFb8GNzCGFQuiKrPsYr-hmZl5O8hYxVk-y9cXuGdkTrUC89_-faqEUSw6bHHB1b3BkIkLNRObwI4vphIge7osJfNg6G1RmPKoEmOoxAuMrEH7yfzjBIMWa_DCjAE0B1vTF0hLqb6MycvIIR",
                                "4.9 ★ (18 loans)",
                                "Pristine Python Edition color graphing calculator with backlit display and rechargeable battery. Essential for Math 51, CS 109, Chem 31, and all midterms or finals."
                        ),
                        new Item(
                                "item-2",
                                "Campbell Biology 12th Edition Hardcover",
                                "books",
                                "Textbooks",
                                2.00,
                                15.00,
                                "Pristine",
                                "Stern Hall • 0.4 mi",
                                "Stanford Campus",
                                "Marcus T.",
                                "Pre-Med • Bio Dept",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuCHzF2ArCYVDUbZmI5k-3Auz7nNqDBA4WqGQ1_r8IIU8jjqDVNVlooZAqi6nibGOpGadYKu5ScBbKKgWnsr9ydHbAltNtedVgEgaBaLKfU3mkvw3s76vF3PLWIMxVCHi2JEtw-gzEwPkPdyYeDOy4DPmUnWHKUK0VL90C9XVINWLVarO1OgZfW830QxaJX5WPLTzllZIizBk3oRRULosxsviytiqWvpYwa3i9q7yI-j",
                                "4.8 ★ (12 loans)",
                                "Clean hardcover edition without tears or missing pages. Has high-yield margin notes for Bio 81 and Bio 82. Great for semester reviews."
                        ),
                        new Item(
                                "item-3",
                                "Sony WH-1000XM4 Noise Cancelling",
                                "tech",
                                "Tech & Electronics",
                                4.00,
                                30.00,
                                "Excellent",
                                "Green Library • 0.1 mi",
                                "Stanford Campus",
                                "Elena R.",
                                "Engineering • Senior",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuDPK1wGgvcZzVIu09lEX1h_MzqjkCm43D_4Gld-fUyrR9IOfggN9H8l2cyKaQMsay2y4vJ_DLobml1FlJd0Ala2y1FLIQdTzFyYBHhYNvgc9JS5svtcYjYuHmxH000cZoAk7B2YX9tpxlpUfQjdI0l-7qkb2jzCotbZSLOEbmhCufoSzHFGW-2d8lPok-lStjxEb0oy5NWMdVzckaT0O6ERhshe9ub0pDFa3hvavx5J",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuBkiquaYFgXakbP2mClmnfb7Va95cC2ekw5VVdqNTX6jzILz4X_lJKi8F7grlVAE-D9QiYeYNyjJfBNCInzQNdNbTdhKGLlWQxRmNdrhjptxFxbyvnmSlNKt4noiBYmHuVR9dyRrTDmvqLd6x9ViR5S6d4p7abPPi0nVk1HllDhaVaucdQJVULxFyeoPQ-MIcFK2c62h2EK7TIpoWfeB3YsuX_Kqfn_xkqORUID6qZG",
                                "5.0 ★ (26 loans)",
                                "Active noise cancellation over-ear headphones. Unrivaled for deep focus in Green Library or noisy dormitory lounges. 30-hour battery life."
                        ),
                        new Item(
                                "item-4",
                                "Heavy Duty Kryptonite U-Lock with Cable",
                                "sports",
                                "Sports & Outdoor",
                                1.50,
                                10.00,
                                "Sturdy",
                                "Tressider Quad • 0.3 mi",
                                "Stanford Campus",
                                "David K.",
                                "Economics • Junior",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuD8LJ5er6DzREDNtgIhPowV_RLu0QJ7E6WBjDYlDPkdDFUGYbzCXQAQv_5mxifD6texvT-FrKICtTvmQPgroK95DNV0jUrDaWNxDd1l-3csq3mAfU02tGPToGD5bh2P1lSXX_gF5WvYXB2pghXiBoURCAhoQSxeyhMiSl8mPumqbg16PpeRys7ZfhVcdEAALS07xemOog2RtG5rnYGZ1_D_opGEsZdWgn7fzbV_BbD3",
                                "4.9 ★ (14 loans)",
                                "Hardened steel bicycle lock with 4ft looped steel cable. Includes 2 keys. Essential for keeping bikes and e-scooters protected on campus."
                        ),
                        new Item(
                                "item-5",
                                "Java Software Solutions (8th Ed)",
                                "books",
                                "Textbooks",
                                2.00,
                                15.00,
                                "Like New",
                                "Gates CS Building • 0.2 mi",
                                "Stanford Campus",
                                "Kevin M.",
                                "CS • Junior",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuDPK1wGgvcZzVIu09lEX1h_MzqjkCm43D_4Gld-fUyrR9IOfggN9H8l2cyKaQMsay2y4vJ_DLobml1FlJd0Ala2y1FLIQdTzFyYBHhYNvgc9JS5svtcYjYuHmxH000cZoAk7B2YX9tpxlpUfQjdI0l-7qkb2jzCotbZSLOEbmhCufoSzHFGW-2d8lPok-lStjxEb0oy5NWMdVzckaT0O6ERhshe9ub0pDFa3hvavx5J",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuDM-3UvkaYlTm0DmafG2spCGujBwntxSSe3OWHJz2R8uZKO50r7sHrasD3L-RWNH5rIg8TcLJD2yYvO4w8Abv0xkONRIw6-ue9a5vRe7wg2Zt8vo1anc-i4vu_mL-m7Tfd8tYeYSzOnTUdi2JqAxO67ILac5J9NFvaF0b6rMr6D2wQUv_sCTRorNe4KdsJtEdMqwUsvQHfiCUTDcJlkq0kCviYFnDezQVCzX1cNNSRq",
                                "4.7 ★ (9 loans)",
                                "Foundations of program design, object-oriented concepts, recursion, and data structures. Recommended for CS 106A/B coursework and midterms."
                        ),
                        new Item(
                                "item-6",
                                "Logitech MX Master 3S Wireless Mouse",
                                "tech",
                                "Tech & Electronics",
                                2.50,
                                25.00,
                                "Pristine",
                                "Design Loft • 0.3 mi",
                                "Stanford Campus",
                                "Jordan T.",
                                "Product Design",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1",
                                "https://lh3.googleusercontent.com/aida-public/AB6AXuD7gwQjV590U9vx14Fk3gWAVGNeM94g7uvPbrLTk2sSK8gny8hVVMT7_0_gm89wFpynlso1Q9OX3izu6Wd4PNJLwwEJNRNjDD2aJQl_5o0aKz5Q1ma_k-mNZwBS7eSiO6fd43lyYEJQMNYJTyVboZBYo00lgRiaz0tR2Zw_aomqYqDQpCp93tw6nEGJjG_rCBVbXdJ1kTE1eCchh_pJHvktAPkVxwhBPFeAVLkhixo7",
                                "4.9 ★ (19 loans)",
                                "Ergonomic quiet click mouse with electromagnetic MagSpeed scroll wheel. Perfect for design studios, CAD, Figma, or programming."
                        )
                );
                itemRepository.saveAll(initialCatalog);
                System.out.println("✅ Preloaded " + initialCatalog.size() + " campus items into MongoDB!");
            }
        };
    }
}

