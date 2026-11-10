package com.campuslend.controller;

import com.campuslend.dto.*;
import com.campuslend.service.AuthService;
import com.campuslend.service.OtpService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;
    private final OtpService otpService;

    @Autowired
    public AuthController(AuthService authService, OtpService otpService) {
        this.authService = authService;
        this.otpService = otpService;
    }

    @PostMapping("/send-otp")
    public ResponseEntity<ApiResponse<String>> sendOtp(@Valid @RequestBody SendOtpRequest request) {
        otpService.generateAndSendOtp(request.getEmail());
        return ResponseEntity.ok(ApiResponse.success(
                "A 6-digit OTP has been sent to your official PSG iTech college email (" + request.getEmail().trim() + "). It expires in 5 minutes.",
                request.getEmail().trim()
        ));
    }

    @PostMapping("/verify-otp")
    public ResponseEntity<ApiResponse<VerifyOtpResponse>> verifyOtp(@Valid @RequestBody VerifyOtpRequest request) {
        VerifyOtpResponse response = otpService.verifyOtp(request.getEmail(), request.getOtp());
        return ResponseEntity.ok(ApiResponse.success(response.getMessage(), response));
    }

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<AuthResponse>> register(@Valid @RequestBody RegisterRequest request) {
        AuthResponse response = authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Account registered successfully", response));
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponse>> login(@Valid @RequestBody LoginRequest request) {
        AuthResponse response = authService.login(request);
        return ResponseEntity.ok(ApiResponse.success("Logged in successfully", response));
    }
}
