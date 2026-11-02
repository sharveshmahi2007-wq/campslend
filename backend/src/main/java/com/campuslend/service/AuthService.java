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
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class AuthService {

    private final StudentRepository studentRepository;
    private final PasswordEncoder passwordEncoder;

    @Autowired
    public AuthService(StudentRepository studentRepository, PasswordEncoder passwordEncoder) {
        this.studentRepository = studentRepository;
        this.passwordEncoder = passwordEncoder;
    }

    public AuthResponse register(RegisterRequest request) {
        String email = request.getEmail().trim().toLowerCase();
        if (!email.endsWith(".edu")) {
            throw new BadRequestException("Must register with a verified university (.edu) email address");
        }

        if (studentRepository.existsByEmail(email)) {
            throw new BadRequestException("An account with email " + email + " already exists");
        }

        if (studentRepository.existsByStudentId(request.getStudentId().trim())) {
            throw new BadRequestException("An account with student ID " + request.getStudentId() + " already exists");
        }

        String hashedPassword = passwordEncoder.encode(request.getPassword());
        Student student = new Student(
                request.getStudentId().trim(),
                request.getName().trim(),
                email,
                hashedPassword,
                request.getDepartment().trim(),
                request.getYear() != null ? request.getYear().trim() : "Junior"
        );

        Student savedStudent = studentRepository.save(student);
        String token = "jwt-simulated-" + UUID.randomUUID();

        return new AuthResponse(token, StudentDto.fromEntity(savedStudent), "Registration successful");
    }

    public AuthResponse login(LoginRequest request) {
        String email = request.getEmail().trim().toLowerCase();
        Student student = studentRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("No student found with email: " + email));

        if (!passwordEncoder.matches(request.getPassword(), student.getPasswordHash())) {
            throw new BadRequestException("Invalid email or password");
        }

        String token = "jwt-simulated-" + UUID.randomUUID();
        return new AuthResponse(token, StudentDto.fromEntity(student), "Login successful");
    }
}

