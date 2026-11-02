package com.campuslend.dto;

public class AuthResponse {

    private String token;
    private StudentDto user;
    private String message;

    public AuthResponse() {
    }

    public AuthResponse(String token, StudentDto user, String message) {
        this.token = token;
        this.user = user;
        this.message = message;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public StudentDto getUser() {
        return user;
    }

    public void setUser(StudentDto user) {
        this.user = user;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}

