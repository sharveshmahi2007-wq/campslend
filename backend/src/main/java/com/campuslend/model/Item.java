package com.campuslend.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Document(collection = "items")
public class Item {

    @Id
    private String id;

    @Indexed
    private String title;

    @Indexed
    private String category; // "books", "tech", "stationery", "sports", "others"

    private String categoryName;

    private double dailyPrice;

    private double depositHold;

    private String condition;

    private String location;

    private String campus;

    private String lenderStudentId;

    private String lenderName;

    private String lenderDept;

    private String lenderAvatar;

    private String image;

    private String rating;

    private String description;

    private boolean isFavorite = false;

    @Indexed
    private boolean isAvailable = true;

    private Instant createdAt = Instant.now();

    public Item() {
    }

    public Item(String id, String title, String category, String categoryName, double dailyPrice,
                double depositHold, String condition, String location, String campus,
                String lenderName, String lenderDept, String lenderAvatar, String image,
                String rating, String description) {
        this.id = id;
        this.title = title;
        this.category = category;
        this.categoryName = categoryName;
        this.dailyPrice = dailyPrice;
        this.depositHold = depositHold;
        this.condition = condition;
        this.location = location;
        this.campus = campus;
        this.lenderName = lenderName;
        this.lenderDept = lenderDept;
        this.lenderAvatar = lenderAvatar;
        this.image = image;
        this.rating = rating;
        this.description = description;
        this.isAvailable = true;
        this.isFavorite = false;
        this.createdAt = Instant.now();
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
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

    public String getCategoryName() {
        return categoryName;
    }

    public void setCategoryName(String categoryName) {
        this.categoryName = categoryName;
    }

    public double getDailyPrice() {
        return dailyPrice;
    }

    public void setDailyPrice(double dailyPrice) {
        this.dailyPrice = dailyPrice;
    }

    public double getDepositHold() {
        return depositHold;
    }

    public void setDepositHold(double depositHold) {
        this.depositHold = depositHold;
    }

    public String getCondition() {
        return condition;
    }

    public void setCondition(String condition) {
        this.condition = condition;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getCampus() {
        return campus;
    }

    public void setCampus(String campus) {
        this.campus = campus;
    }

    public String getLenderStudentId() {
        return lenderStudentId;
    }

    public void setLenderStudentId(String lenderStudentId) {
        this.lenderStudentId = lenderStudentId;
    }

    public String getLenderName() {
        return lenderName;
    }

    public void setLenderName(String lenderName) {
        this.lenderName = lenderName;
    }

    public String getLenderDept() {
        return lenderDept;
    }

    public void setLenderDept(String lenderDept) {
        this.lenderDept = lenderDept;
    }

    public String getLenderAvatar() {
        return lenderAvatar;
    }

    public void setLenderAvatar(String lenderAvatar) {
        this.lenderAvatar = lenderAvatar;
    }

    public String getImage() {
        return image;
    }

    public void setImage(String image) {
        this.image = image;
    }

    public String getRating() {
        return rating;
    }

    public void setRating(String rating) {
        this.rating = rating;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public boolean isFavorite() {
        return isFavorite;
    }

    public void setFavorite(boolean favorite) {
        isFavorite = favorite;
    }

    public boolean isAvailable() {
        return isAvailable;
    }

    public void setAvailable(boolean available) {
        isAvailable = available;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
}

