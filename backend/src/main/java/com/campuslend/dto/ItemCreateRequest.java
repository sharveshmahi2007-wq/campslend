package com.campuslend.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class ItemCreateRequest {

    @NotBlank(message = "Title is required")
    private String title;

    @NotBlank(message = "Category is required")
    private String category; // "books", "tech", "stationery", "sports", "others"

    private String condition = "Like New";

    @NotNull(message = "Daily price is required")
    @Min(value = 0, message = "Daily price must be positive")
    private Double dailyPrice = 3.00;

    @NotNull(message = "Deposit is required")
    @Min(value = 0, message = "Deposit must be non-negative")
    private Double depositHold = 20.00;

    private String location = "Wilbur Hall";

    private String description = "Student item in good working condition.";

    private String lenderStudentId;

    private String imageUrl;

    public ItemCreateRequest() {
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public String getCondition() {
        return condition;
    }

    public void setCondition(String condition) {
        this.condition = condition;
    }

    public Double getDailyPrice() {
        return dailyPrice;
    }

    public void setDailyPrice(Double dailyPrice) {
        this.dailyPrice = dailyPrice;
    }

    public Double getDepositHold() {
        return depositHold;
    }

    public void setDepositHold(Double depositHold) {
        this.depositHold = depositHold;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getLenderStudentId() {
        return lenderStudentId;
    }

    public void setLenderStudentId(String lenderStudentId) {
        this.lenderStudentId = lenderStudentId;
    }

    public String getImageUrl() {
        return imageUrl;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }
}

