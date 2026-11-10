package com.campuslend.dto;

public class VerifyOtpResponse {

    private boolean verified;
    private String email;
    private String verificationToken;
    private String message;

    public VerifyOtpResponse() {
    }

    public VerifyOtpResponse(boolean verified, String email, String verificationToken, String message) {
        this.verified = verified;
        this.email = email;
        this.verificationToken = verificationToken;
        this.message = message;
    }

    public boolean isVerified() {
        return verified;
    }

    public void setVerified(boolean verified) {
        this.verified = verified;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getVerificationToken() {
        return verificationToken;
    }

    public void setVerificationToken(String verificationToken) {
        this.verificationToken = verificationToken;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}

