package com.campuslend.model;

import com.campuslend.model.enums.LoanStatus;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Document(collection = "loans")
public class Loan {

    @Id
    private String id;

    @Indexed
    private String itemId;

    private String itemTitle;

    private String itemImage;

    @Indexed
    private String borrowerStudentId;

    private String borrowerName;

    private String borrowerDept;

    @Indexed
    private String ownerStudentId;

    private String ownerName;

    private String ownerDept;

    private int borrowDays = 3;

    private double dailyPrice;

    private double depositHeld;

    private double totalRentalCost;

    @Indexed
    private LoanStatus status = LoanStatus.REQUESTED;

    private String pickupLocation;

    private String securityToken;

    private String note;

    private Instant requestedAt = Instant.now();

    private Instant approvedAt;

    private Instant dueAt;

    private Instant returnedAt;

    public Loan() {
    }

    public Loan(String itemId, String itemTitle, String itemImage, String borrowerStudentId,
                String borrowerName, String borrowerDept, String ownerStudentId, String ownerName,
                String ownerDept, int borrowDays, double dailyPrice, double depositHeld,
                String pickupLocation, String note) {
        this.itemId = itemId;
        this.itemTitle = itemTitle;
        this.itemImage = itemImage;
        this.borrowerStudentId = borrowerStudentId;
        this.borrowerName = borrowerName;
        this.borrowerDept = borrowerDept;
        this.ownerStudentId = ownerStudentId;
        this.ownerName = ownerName;
        this.ownerDept = ownerDept;
        this.borrowDays = borrowDays;
        this.dailyPrice = dailyPrice;
        this.depositHeld = depositHeld;
        this.totalRentalCost = dailyPrice * borrowDays;
        this.pickupLocation = pickupLocation;
        this.note = note;
        this.status = LoanStatus.REQUESTED;
        this.securityToken = "LL-STAN-" + (1000 + (int)(Math.random() * 9000));
        this.requestedAt = Instant.now();
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getItemId() {
        return itemId;
    }

    public void setItemId(String itemId) {
        this.itemId = itemId;
    }

    public String getItemTitle() {
        return itemTitle;
    }

    public void setItemTitle(String itemTitle) {
        this.itemTitle = itemTitle;
    }

    public String getItemImage() {
        return itemImage;
    }

    public void setItemImage(String itemImage) {
        this.itemImage = itemImage;
    }

    public String getBorrowerStudentId() {
        return borrowerStudentId;
    }

    public void setBorrowerStudentId(String borrowerStudentId) {
        this.borrowerStudentId = borrowerStudentId;
    }

    public String getBorrowerName() {
        return borrowerName;
    }

    public void setBorrowerName(String borrowerName) {
        this.borrowerName = borrowerName;
    }

    public String getBorrowerDept() {
        return borrowerDept;
    }

    public void setBorrowerDept(String borrowerDept) {
        this.borrowerDept = borrowerDept;
    }

    public String getOwnerStudentId() {
        return ownerStudentId;
    }

    public void setOwnerStudentId(String ownerStudentId) {
        this.ownerStudentId = ownerStudentId;
    }

    public String getOwnerName() {
        return ownerName;
    }

    public void setOwnerName(String ownerName) {
        this.ownerName = ownerName;
    }

    public String getOwnerDept() {
        return ownerDept;
    }

    public void setOwnerDept(String ownerDept) {
        this.ownerDept = ownerDept;
    }

    public int getBorrowDays() {
        return borrowDays;
    }

    public void setBorrowDays(int borrowDays) {
        this.borrowDays = borrowDays;
    }

    public double getDailyPrice() {
        return dailyPrice;
    }

    public void setDailyPrice(double dailyPrice) {
        this.dailyPrice = dailyPrice;
    }

    public double getDepositHeld() {
        return depositHeld;
    }

    public void setDepositHeld(double depositHeld) {
        this.depositHeld = depositHeld;
    }

    public double getTotalRentalCost() {
        return totalRentalCost;
    }

    public void setTotalRentalCost(double totalRentalCost) {
        this.totalRentalCost = totalRentalCost;
    }

    public LoanStatus getStatus() {
        return status;
    }

    public void setStatus(LoanStatus status) {
        this.status = status;
    }

    public String getPickupLocation() {
        return pickupLocation;
    }

    public void setPickupLocation(String pickupLocation) {
        this.pickupLocation = pickupLocation;
    }

    public String getSecurityToken() {
        return securityToken;
    }

    public void setSecurityToken(String securityToken) {
        this.securityToken = securityToken;
    }

    public String getNote() {
        return note;
    }

    public void setNote(String note) {
        this.note = note;
    }

    public Instant getRequestedAt() {
        return requestedAt;
    }

    public void setRequestedAt(Instant requestedAt) {
        this.requestedAt = requestedAt;
    }

    public Instant getApprovedAt() {
        return approvedAt;
    }

    public void setApprovedAt(Instant approvedAt) {
        this.approvedAt = approvedAt;
    }

    public Instant getDueAt() {
        return dueAt;
    }

    public void setDueAt(Instant dueAt) {
        this.dueAt = dueAt;
    }

    public Instant getReturnedAt() {
        return returnedAt;
    }

    public void setReturnedAt(Instant returnedAt) {
        this.returnedAt = returnedAt;
    }
}

