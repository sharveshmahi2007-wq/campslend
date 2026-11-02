package com.campuslend.dto;

import com.campuslend.model.Student;
import com.campuslend.model.enums.Role;

public class StudentDto {

    private String id;
    private String studentId;
    private String name;
    private String email;
    private String department;
    private String year;
    private String dorm;
    private String campus;
    private String phone;
    private Role role;
    private int itemsLentCount;
    private int itemsBorrowedCount;
    private double trustRating;

    public StudentDto() {
    }

    public static StudentDto fromEntity(Student s) {
        if (s == null) return null;
        StudentDto dto = new StudentDto();
        dto.setId(s.getId());
        dto.setStudentId(s.getStudentId());
        dto.setName(s.getName());
        dto.setEmail(s.getEmail());
        dto.setDepartment(s.getDepartment());
        dto.setYear(s.getYear());
        dto.setDorm(s.getDorm());
        dto.setCampus(s.getCampus());
        dto.setPhone(s.getPhone());
        dto.setRole(s.getRole());
        dto.setItemsLentCount(s.getItemsLentCount());
        dto.setItemsBorrowedCount(s.getItemsBorrowedCount());
        dto.setTrustRating(s.getTrustRating());
        return dto;
    }

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
}

