package com.campuslend.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Document(collection = "otp_tokens")
public class OtpToken {

    @Id
    private String id;

    @Indexed(unique = true)
    private String email;

    private String otpHash;

    private String salt;

    private Instant createdAt;

    private Instant expiresAt;

    private Instant lastSentAt;

    private int attempts = 0;

    private boolean verified = false;

    private String verificationToken;

    public OtpToken() {
    }

    public OtpToken(String email, String otpHash, String salt, Instant expiresAt) {
        this.email = email;
        this.otpHash = otpHash;
        this.salt = salt;
        this.createdAt = Instant.now();
        this.lastSentAt = Instant.now();
        this.expiresAt = expiresAt;
        this.attempts = 0;
        this.verified = false;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getOtpHash() {
        return otpHash;
    }

    public void setOtpHash(String otpHash) {
        this.otpHash = otpHash;
    }

    public String getSalt() {
        return salt;
    }

    public void setSalt(String salt) {
        this.salt = salt;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public Instant getExpiresAt() {
        return expiresAt;
    }

    public void setExpiresAt(Instant expiresAt) {
        this.expiresAt = expiresAt;
    }

    public Instant getLastSentAt() {
        return lastSentAt;
    }

    public void setLastSentAt(Instant lastSentAt) {
        this.lastSentAt = lastSentAt;
    }

    public int getAttempts() {
        return attempts;
    }

    public void setAttempts(int attempts) {
        this.attempts = attempts;
    }

    public boolean isVerified() {
        return verified;
    }

    public void setVerified(boolean verified) {
        this.verified = verified;
    }

    public String getVerificationToken() {
        return verificationToken;
    }

    public void setVerificationToken(String verificationToken) {
        this.verificationToken = verificationToken;
    }

    public boolean isExpired() {
        return Instant.now().isAfter(this.expiresAt);
    }
}

