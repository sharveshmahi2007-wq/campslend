package com.campuslend.model;

import com.campuslend.model.enums.Role;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Document(collection = "students")
public class Student {

    @Id
    private String id;

    @Indexed(unique = true)
    private String studentId;

    private String name;

    @Indexed(unique = true)
    private String email;

    private String passwordHash;

    private String department;

    private String year;

    private String dorm;

    private String campus;

    private String phone;

    private Role role = Role.STUDENT;

    private int itemsLentCount = 0;

    private int itemsBorrowedCount = 0;

    private double trustRating = 5.0;

    private Instant createdAt = Instant.now();

    private Instant updatedAt = Instant.now();

    public Student() {
    }

    public Student(String studentId, String name, String email, String passwordHash, String department, String year) {
        this.studentId = studentId;
        this.name = name;
        this.email = email;
        this.passwordHash = passwordHash;
        this.department = department;
        this.year = year;
        this.campus = "Stanford University";
        this.dorm = "Wilbur Hall 304";
        this.phone = "+1 (650) 555-0194";
        this.role = Role.STUDENT;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getStudentId() {
        return studentId;
    }

    public void setStudentId(String studentId) {
        this.studentId = studentId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public void setPasswordHash(String passwordHash) {
        this.passwordHash = passwordHash;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public String getYear() {
        return year;
    }

    public void setYear(String year) {
        this.year = year;
    }

    public String getDorm() {
        return dorm;
    }

    public void setDorm(String dorm) {
        this.dorm = dorm;
    }

    public String getCampus() {
        return campus;
    }

    public void setCampus(String campus) {
        this.campus = campus;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public Role getRole() {
        return role;
    }

    public void setRole(Role role) {
        this.role = role;
    }

    public int getItemsLentCount() {
        return itemsLentCount;
    }

    public void setItemsLentCount(int itemsLentCount) {
        this.itemsLentCount = itemsLentCount;
    }

    public int getItemsBorrowedCount() {
        return itemsBorrowedCount;
    }

    public void setItemsBorrowedCount(int itemsBorrowedCount) {
        this.itemsBorrowedCount = itemsBorrowedCount;
    }

    public double getTrustRating() {
        return trustRating;
    }

    public void setTrustRating(double trustRating) {
        this.trustRating = trustRating;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }
}

