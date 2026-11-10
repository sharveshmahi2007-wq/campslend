package com.campuslend.service;

import com.campuslend.dto.AuthResponse;
import com.campuslend.dto.LoginRequest;
import com.campuslend.dto.RegisterRequest;
import com.campuslend.dto.StudentDto;
import com.campuslend.exception.BadRequestException;
import com.campuslend.exception.ResourceNotFoundException;
import com.campuslend.model.Student;
import com.campuslend.repository.StudentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class AuthService {

    private final StudentRepository studentRepository;
    private final PasswordEncoder passwordEncoder;
    private final OtpService otpService;

    @Value("${app.security.college-domain:psgitech.ac.in}")
    private String collegeDomain;

    @Autowired
    public AuthService(StudentRepository studentRepository,
                       PasswordEncoder passwordEncoder,
                       OtpService otpService) {
        this.studentRepository = studentRepository;
        this.passwordEncoder = passwordEncoder;
        this.otpService = otpService;
    }

    public AuthResponse register(RegisterRequest request) {
        // Enforce PSG iTech official domain
        String email = otpService.normalizeAndValidateDomain(request.getEmail());

        // Validate that OTP verification was successfully completed for this email
        if (request.getVerificationToken() != null && !request.getVerificationToken().isBlank()) {
            boolean valid = otpService.validateVerificationToken(email, request.getVerificationToken().trim());
            if (!valid) {
                throw new BadRequestException("Invalid or expired OTP verification token. Please verify your email again.");
            }
        } else {
            throw new BadRequestException("Email verification required. Please verify your PSG iTech email with OTP first.");
        }

        if (studentRepository.existsByEmail(email)) {
            throw new BadRequestException("An account with email " + email + " already exists. Please log in.");
        }

        if (studentRepository.existsByStudentId(request.getStudentId().trim())) {
            throw new BadRequestException("An account with student roll number " + request.getStudentId() + " already exists.");
        }

        // Secure password hashing with BCrypt
        String hashedPassword = passwordEncoder.encode(request.getPassword());
        Student student = new Student(
                request.getStudentId().trim(),
                request.getName().trim(),
                email,
                hashedPassword,
                request.getDepartment().trim(),
                request.getYear() != null ? request.getYear().trim() : "Junior"
        );
        student.setCampus("PSG Institute of Technology and Applied Research");
        student.setDorm("PSG iTech Hostel");

        Student savedStudent = studentRepository.save(student);
        String token = "jwt-psgitech-" + UUID.randomUUID();

        return new AuthResponse(token, StudentDto.fromEntity(savedStudent), "Registration successful");
    }

    public AuthResponse login(LoginRequest request) {
        String email = otpService.normalizeAndValidateDomain(request.getEmail());

        Student student = studentRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("No registered student found with email: " + email + ". Please register first."));

        if (!passwordEncoder.matches(request.getPassword(), student.getPasswordHash())) {
            throw new BadRequestException("Invalid email or password.");
        }

        String token = "jwt-psgitech-" + UUID.randomUUID();
        return new AuthResponse(token, StudentDto.fromEntity(student), "Login successful");
    }
}
