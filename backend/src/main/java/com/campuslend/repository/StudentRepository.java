package com.campuslend.repository;

import com.campuslend.model.Student;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface StudentRepository extends MongoRepository<Student, String> {

    Optional<Student> findByEmail(String email);

    Optional<Student> findByStudentId(String studentId);

    boolean existsByEmail(String email);

    boolean existsByStudentId(String studentId);
}

