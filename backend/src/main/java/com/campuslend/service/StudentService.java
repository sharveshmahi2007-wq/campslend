package com.campuslend.service;

import com.campuslend.dto.StudentDto;
import com.campuslend.exception.ResourceNotFoundException;
import com.campuslend.model.Student;
import com.campuslend.repository.StudentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Service
public class StudentService {

    private final StudentRepository studentRepository;

    @Autowired
    public StudentService(StudentRepository studentRepository) {
        this.studentRepository = studentRepository;
    }

    public StudentDto getProfile(String emailOrStudentId) {
        Student student = studentRepository.findByEmail(emailOrStudentId.toLowerCase())
                .or(() -> studentRepository.findByStudentId(emailOrStudentId))
                .orElseThrow(() -> new ResourceNotFoundException("Student profile not found: " + emailOrStudentId));

        return StudentDto.fromEntity(student);
    }

    public StudentDto updateProfile(String studentId, StudentDto updateDto) {
        Student student = studentRepository.findByStudentId(studentId)
                .or(() -> studentRepository.findByEmail(studentId.toLowerCase()))
                .orElseThrow(() -> new ResourceNotFoundException("Student not found: " + studentId));

        if (updateDto.getName() != null && !updateDto.getName().isBlank()) {
            student.setName(updateDto.getName().trim());
        }
        if (updateDto.getDorm() != null && !updateDto.getDorm().isBlank()) {
            student.setDorm(updateDto.getDorm().trim());
        }
        if (updateDto.getPhone() != null && !updateDto.getPhone().isBlank()) {
            student.setPhone(updateDto.getPhone().trim());
        }
        if (updateDto.getDepartment() != null && !updateDto.getDepartment().isBlank()) {
            student.setDepartment(updateDto.getDepartment().trim());
        }
        if (updateDto.getYear() != null && !updateDto.getYear().isBlank()) {
            student.setYear(updateDto.getYear().trim());
        }

        student.setUpdatedAt(Instant.now());
        Student saved = studentRepository.save(student);
        return StudentDto.fromEntity(saved);
    }
}

