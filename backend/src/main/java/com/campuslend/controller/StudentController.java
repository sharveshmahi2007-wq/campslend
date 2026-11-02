package com.campuslend.controller;

import com.campuslend.dto.ApiResponse;
import com.campuslend.dto.StudentDto;
import com.campuslend.service.StudentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/students")
public class StudentController {

    private final StudentService studentService;

    @Autowired
    public StudentController(StudentService studentService) {
        this.studentService = studentService;
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<StudentDto>> getCurrentStudent(
            @RequestParam(defaultValue = "alex.chen@stanford.edu") String emailOrId) {
        StudentDto profile = studentService.getProfile(emailOrId);
        return ResponseEntity.ok(ApiResponse.success(profile));
    }

    @PutMapping("/me")
    public ResponseEntity<ApiResponse<StudentDto>> updateProfile(
            @RequestParam(defaultValue = "SU-9824102") String studentId,
            @RequestBody StudentDto updateDto) {
        StudentDto updated = studentService.updateProfile(studentId, updateDto);
        return ResponseEntity.ok(ApiResponse.success("Profile updated successfully", updated));
    }
}

