package com.campuslend.service;

import com.campuslend.dto.VerifyOtpResponse;
import com.campuslend.exception.BadRequestException;
import com.campuslend.model.OtpToken;
import com.campuslend.repository.OtpTokenRepository;
import com.campuslend.repository.StudentRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Optional;
import java.util.UUID;

@Service
public class OtpService {

    private static final Logger log = LoggerFactory.getLogger(OtpService.class);
    private static final SecureRandom secureRandom = new SecureRandom();

    private final OtpTokenRepository otpTokenRepository;
    private final StudentRepository studentRepository;
    private final EmailService emailService;

    @Value("${app.security.college-domain:psgitech.ac.in}")
    private String collegeDomain;

    @Value("${app.security.otp.expiration-minutes:5}")
    private int expirationMinutes;

    @Value("${app.security.otp.max-attempts:5}")
    private int maxAttempts;

    @Value("${app.security.otp.resend-cooldown-seconds:60}")
    private int cooldownSeconds;

    @Autowired
    public OtpService(OtpTokenRepository otpTokenRepository,
                      StudentRepository studentRepository,
                      EmailService emailService) {
        this.otpTokenRepository = otpTokenRepository;
        this.studentRepository = studentRepository;
        this.emailService = emailService;
    }

    /**
     * Generates and dispatches a 6-digit OTP to a valid @psgitech.ac.in college email.
     */
    public void generateAndSendOtp(String rawEmail) {
        String email = normalizeAndValidateDomain(rawEmail);

        // Check duplicate registration
        if (studentRepository.existsByEmail(email)) {
            throw new BadRequestException("An account with " + email + " is already registered. Please proceed to log in.");
        }

        // Check resend cooldown
        Optional<OtpToken> existingOpt = otpTokenRepository.findByEmail(email);
        if (existingOpt.isPresent()) {
            OtpToken existing = existingOpt.get();
            if (existing.getLastSentAt() != null) {
                long elapsed = Duration.between(existing.getLastSentAt(), Instant.now()).getSeconds();
                if (elapsed < cooldownSeconds) {
                    long waitTime = cooldownSeconds - elapsed;
                    throw new BadRequestException("Please wait " + waitTime + " seconds before requesting a new OTP.");
                }
            }
        }

        // Generate 6-digit OTP
        int code = 100000 + secureRandom.nextInt(900000);
        String plainOtp = String.valueOf(code);

        // Hash OTP with Salt (Never store plain text OTP)
        String salt = UUID.randomUUID().toString().replace("-", "");
        String otpHash = hashOtp(plainOtp, salt);

        Instant expiresAt = Instant.now().plus(Duration.ofMinutes(expirationMinutes));

        OtpToken otpToken = existingOpt.orElseGet(OtpToken::new);
        otpToken.setEmail(email);
        otpToken.setOtpHash(otpHash);
        otpToken.setSalt(salt);
        otpToken.setCreatedAt(Instant.now());
        otpToken.setLastSentAt(Instant.now());
        otpToken.setExpiresAt(expiresAt);
        otpToken.setAttempts(0);
        otpToken.setVerified(false);
        otpToken.setVerificationToken(null);

        otpTokenRepository.save(otpToken);

        // Send OTP via configured EmailService (or log to console)
        emailService.sendOtpEmail(email, plainOtp);
    }

    /**
     * Verifies the provided 6-digit OTP. Enforces 5-minute expiration, max 5 attempts, and single-use.
     */
    public VerifyOtpResponse verifyOtp(String rawEmail, String plainOtp) {
        String email = normalizeAndValidateDomain(rawEmail);

        if (plainOtp == null || !plainOtp.matches("^\\d{6}$")) {
            throw new BadRequestException("OTP must be exactly 6 digits.");
        }

        OtpToken token = otpTokenRepository.findByEmail(email)
                .orElseThrow(() -> new BadRequestException("No active OTP request found for " + email + ". Please request an OTP first."));

        // Check if already verified
        if (token.isVerified() && token.getVerificationToken() != null) {
            return new VerifyOtpResponse(true, email, token.getVerificationToken(), "Email already verified.");
        }

        // Check attempt limit
        if (token.getAttempts() >= maxAttempts) {
            throw new BadRequestException("Maximum OTP verification attempts (" + maxAttempts + ") exceeded. Please request a new OTP.");
        }

        // Check expiration
        if (token.isExpired()) {
            throw new BadRequestException("OTP has expired (valid for " + expirationMinutes + " minutes). Please request a new OTP.");
        }

        // Compare hashes
        String candidateHash = hashOtp(plainOtp.trim(), token.getSalt());
        if (!candidateHash.equals(token.getOtpHash())) {
            int currentAttempts = token.getAttempts() + 1;
            token.setAttempts(currentAttempts);
            otpTokenRepository.save(token);

            int remaining = Math.max(0, maxAttempts - currentAttempts);
            if (remaining == 0) {
                throw new BadRequestException("Incorrect OTP. Maximum attempts reached. Please request a new OTP.");
            }
            throw new BadRequestException("Incorrect OTP. " + remaining + " attempt(s) remaining.");
        }

        // Verification successful: Single-use invalidation of OTP hash
        String verificationToken = UUID.randomUUID().toString();
        token.setVerified(true);
        token.setVerificationToken(verificationToken);
        token.setOtpHash(null); // Invalidate OTP for single-use guarantee
        token.setAttempts(0);
        otpTokenRepository.save(token);

        log.info("[OtpService] Successfully verified OTP for PSG iTech student: {}", email);
        return new VerifyOtpResponse(true, email, verificationToken, "College email verified successfully.");
    }

    /**
     * Validates that an email has been verified before completing registration.
     */
    public boolean validateVerificationToken(String rawEmail, String verificationToken) {
        if (verificationToken == null || verificationToken.isBlank()) {
            return false;
        }
        String email = rawEmail.trim().toLowerCase();
        Optional<OtpToken> opt = otpTokenRepository.findByEmail(email);
        if (opt.isEmpty()) return false;
        OtpToken token = opt.get();
        return token.isVerified() && verificationToken.equals(token.getVerificationToken());
    }

    /**
     * Validates that the email ends with the designated college domain.
     */
    public String normalizeAndValidateDomain(String rawEmail) {
        if (rawEmail == null || rawEmail.trim().isEmpty()) {
            throw new BadRequestException("College email cannot be empty.");
        }
        String email = rawEmail.trim().toLowerCase();
        String targetDomain = collegeDomain.trim().toLowerCase();

        if (!email.endsWith("@" + targetDomain)) {
            throw new BadRequestException("Access restricted: Only official PSG iTech email addresses (@" + targetDomain + ") are allowed. Personal emails (Gmail, Yahoo, Outlook) are not permitted.");
        }
        return email;
    }

    private String hashOtp(String otp, String salt) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest((otp + ":" + salt).getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }
}

