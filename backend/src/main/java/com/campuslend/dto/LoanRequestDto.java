package com.campuslend.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class LoanRequestDto {

    @NotBlank(message = "Item ID is required")
    private String itemId;

    @NotBlank(message = "Borrower student ID is required")
    private String borrowerStudentId;

    @NotNull(message = "Borrow days count is required")
    @Min(value = 1, message = "Borrow days must be at least 1")
    private Integer borrowDays = 3;

    private String note;

    public LoanRequestDto() {
    }

    public String getItemId() {
        return itemId;
    }

    public void setItemId(String itemId) {
        this.itemId = itemId;
    }

    public String getBorrowerStudentId() {
        return borrowerStudentId;
    }

    public void setBorrowerStudentId(String borrowerStudentId) {
        this.borrowerStudentId = borrowerStudentId;
    }

    public Integer getBorrowDays() {
        return borrowDays;
    }

    public void setBorrowDays(Integer borrowDays) {
        this.borrowDays = borrowDays;
    }

    public String getNote() {
        return note;
    }

    public void setNote(String note) {
        this.note = note;
    }
}

