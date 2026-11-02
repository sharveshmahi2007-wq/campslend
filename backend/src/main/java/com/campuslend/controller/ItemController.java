package com.campuslend.controller;

import com.campuslend.dto.ApiResponse;
import com.campuslend.dto.ItemCreateRequest;
import com.campuslend.model.Item;
import com.campuslend.service.ItemService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/items")
public class ItemController {

    private final ItemService itemService;

    @Autowired
    public ItemController(ItemService itemService) {
        this.itemService = itemService;
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<Item>>> getAllItems(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String query,
            @RequestParam(required = false) Double maxPrice,
            @RequestParam(required = false) String hub,
            @RequestParam(required = false) Boolean onlyAvailable) {
        List<Item> items = itemService.getItems(category, query, maxPrice, hub, onlyAvailable);
        return ResponseEntity.ok(ApiResponse.success(items));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Item>> getItemById(@PathVariable String id) {
        Item item = itemService.getItemById(id);
        return ResponseEntity.ok(ApiResponse.success(item));
    }

    @PostMapping
    public ResponseEntity<ApiResponse<Item>> createItem(@Valid @RequestBody ItemCreateRequest request) {
        Item created = itemService.createItem(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Listing published successfully", created));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteItem(@PathVariable String id) {
        itemService.deleteItem(id);
        return ResponseEntity.ok(ApiResponse.success("Item listing removed", null));
    }

    @PostMapping("/{id}/favorite")
    public ResponseEntity<ApiResponse<Item>> toggleFavorite(@PathVariable String id) {
        Item updated = itemService.toggleFavorite(id);
        return ResponseEntity.ok(ApiResponse.success(updated.isFavorite() ? "Added to wishlist" : "Removed from wishlist", updated));
    }
}

