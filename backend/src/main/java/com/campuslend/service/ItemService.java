package com.campuslend.service;

import com.campuslend.dto.ItemCreateRequest;
import com.campuslend.exception.ResourceNotFoundException;
import com.campuslend.model.Item;
import com.campuslend.model.Student;
import com.campuslend.repository.ItemRepository;
import com.campuslend.repository.StudentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ItemService {

    private final ItemRepository itemRepository;
    private final StudentRepository studentRepository;

    @Autowired
    public ItemService(ItemRepository itemRepository, StudentRepository studentRepository) {
        this.itemRepository = itemRepository;
        this.studentRepository = studentRepository;
    }

    public List<Item> getItems(String category, String query, Double maxPrice, String hub, Boolean onlyAvailable) {
        List<Item> allItems = itemRepository.findAll();

        return allItems.stream()
                .filter(item -> category == null || category.equalsIgnoreCase("all") || item.getCategory().equalsIgnoreCase(category))
                .filter(item -> {
                    if (query == null || query.isBlank()) return true;
                    String q = query.toLowerCase().trim();
                    return item.getTitle().toLowerCase().contains(q) ||
                           item.getDescription().toLowerCase().contains(q) ||
                           item.getLenderName().toLowerCase().contains(q);
                })
                .filter(item -> maxPrice == null || item.getDailyPrice() <= maxPrice)
                .filter(item -> hub == null || hub.equalsIgnoreCase("all") || item.getLocation().toLowerCase().contains(hub.toLowerCase()))
                .filter(item -> onlyAvailable == null || !onlyAvailable || item.isAvailable())
                .collect(Collectors.toList());
    }

    public Item getItemById(String id) {
        return itemRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Item not found with id: " + id));
    }

    public Item createItem(ItemCreateRequest request) {
        String catName = mapCategoryName(request.getCategory());
        String lenderName = "Alex Rivera";
        String lenderDept = "Junior • Computer Science";
        String lenderAvatar = "https://lh3.googleusercontent.com/aida-public/AB6AXuCHidFGGvejNyhkUBYrLtdf6YBBJH4cdUC8PrAvMSsLsYw29f3rxNOr1LXFSuNGwGsWjv-ou9bedavLx1oiQXsiW3MD674jEP9umUigltN6OXY-sEur0CQveiqITJGNH2LX-cl2jcU0Vef-R_KhMIEo1PwG_hbf0mrS88phMWaoVA6h74QfX_S0Km9Ne14pch4EEQ08E86vS_bWV-4UiNF6-5rhOjPAEsh2hEdwtOo1";

        if (request.getLenderStudentId() != null) {
            studentRepository.findByStudentId(request.getLenderStudentId()).ifPresent(student -> {
                // use actual student info if provided
            });
        }

        String finalImage = (request.getImageUrl() != null && !request.getImageUrl().trim().isEmpty())
                ? request.getImageUrl()
                : "https://lh3.googleusercontent.com/aida-public/AB6AXuB1HLeRSpdgX3LeoQ9mKLRt0X8SHRfjH-LLTBXn9iGVr2G2W-sbi6wLcDAmJHmAkp9a45-S86r-gBeooxf-ZHCzhnScTw_fb64wyFXHeYIB6Y2rhFj9Xwq8H3Jyo1MiRTL6sYNsNbbOLooGqLV8-tsClXqov9PCWGaswUaD8ATn6-PiMI7rw0UjAlEze1KZU8_A4u1qY4KyORJbuyQs7NNmzKB8rgmOz4INaa5dseI2";

        Item item = new Item(
                "item-" + System.currentTimeMillis(),
                request.getTitle(),
                request.getCategory(),
                catName,
                request.getDailyPrice() != null ? request.getDailyPrice() : 3.00,
                request.getDepositHold() != null ? request.getDepositHold() : 20.00,
                request.getCondition() != null ? request.getCondition() : "Like New",
                request.getLocation() != null ? request.getLocation() : "Wilbur Hall",
                "Stanford Campus",
                lenderName,
                lenderDept,
                lenderAvatar,
                finalImage,
                "5.0 ★ (New)",
                request.getDescription()
        );

        return itemRepository.save(item);
    }

    public void deleteItem(String id) {
        if (!itemRepository.existsById(id)) {
            throw new ResourceNotFoundException("Item not found: " + id);
        }
        itemRepository.deleteById(id);
    }

    public Item toggleFavorite(String id) {
        Item item = getItemById(id);
        item.setFavorite(!item.isFavorite());
        return itemRepository.save(item);
    }

    private String mapCategoryName(String categoryKey) {
        if (categoryKey == null) return "General";
        return switch (categoryKey.toLowerCase()) {
            case "books" -> "Textbooks";
            case "tech" -> "Tech & Electronics";
            case "stationery" -> "Calculators & Lab";
            case "sports" -> "Sports & Outdoor";
            default -> "Dorm Living";
        };
    }
}

