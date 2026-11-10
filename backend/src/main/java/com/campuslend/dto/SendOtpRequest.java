package com.campuslend.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public class SendOtpRequest {

    @NotBlank(message = "College email is required")
    @Email(message = "Invalid email format")
    private String email;

    public SendOtpRequest() {
    }

    public SendOtpRequest(String email) {
        this.email = email;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}

