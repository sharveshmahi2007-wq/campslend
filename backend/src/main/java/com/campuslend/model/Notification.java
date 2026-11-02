package com.campuslend.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Document(collection = "notifications")
public class Notification {

    @Id
    private String id;

    @Indexed
    private String recipientStudentId;

    private String title;

    private String description;

    private String type; // "DUE_SOON", "REQUEST", "HANDOVER_CONFIRMED"

    private boolean isRead = false;

    private Instant createdAt = Instant.now();

    public Notification() {
    }

    public Notification(String recipientStudentId, String title, String description, String type) {
        this.recipientStudentId = recipientStudentId;
        this.title = title;
        this.description = description;
        this.type = type;
        this.isRead = false;
        this.createdAt = Instant.now();
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getRecipientStudentId() {
        return recipientStudentId;
    }

    public void setRecipientStudentId(String recipientStudentId) {
        this.recipientStudentId = recipientStudentId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public boolean isRead() {
        return isRead;
    }

    public void setRead(boolean read) {
        isRead = read;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
}

