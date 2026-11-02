package com.campuslend.repository;

import com.campuslend.model.Loan;
import com.campuslend.model.enums.LoanStatus;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LoanRepository extends MongoRepository<Loan, String> {

    List<Loan> findByBorrowerStudentId(String borrowerStudentId);

    List<Loan> findByOwnerStudentId(String ownerStudentId);

    List<Loan> findByOwnerStudentIdAndStatus(String ownerStudentId, LoanStatus status);

    List<Loan> findByBorrowerStudentIdAndStatus(String borrowerStudentId, LoanStatus status);

    List<Loan> findByItemIdAndStatus(String itemId, LoanStatus status);
}

