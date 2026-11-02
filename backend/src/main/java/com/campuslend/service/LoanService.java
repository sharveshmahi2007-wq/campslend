package com.campuslend.service;

import com.campuslend.dto.LoanRequestDto;
import com.campuslend.exception.BadRequestException;
import com.campuslend.exception.ResourceNotFoundException;
import com.campuslend.model.Item;
import com.campuslend.model.Loan;
import com.campuslend.model.Student;
import com.campuslend.model.enums.LoanStatus;
import com.campuslend.repository.ItemRepository;
import com.campuslend.repository.LoanRepository;
import com.campuslend.repository.StudentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Service
public class LoanService {

    private final LoanRepository loanRepository;
    private final ItemRepository itemRepository;
    private final StudentRepository studentRepository;

    @Autowired
    public LoanService(LoanRepository loanRepository, ItemRepository itemRepository, StudentRepository studentRepository) {
        this.loanRepository = loanRepository;
        this.itemRepository = itemRepository;
        this.studentRepository = studentRepository;
    }

    public Loan createLoanRequest(LoanRequestDto request) {
        Item item = itemRepository.findById(request.getItemId())
                .orElseThrow(() -> new ResourceNotFoundException("Item not found: " + request.getItemId()));

        if (!item.isAvailable()) {
            throw new BadRequestException("Item is currently not available for borrowing");
        }

        String borrowerName = "Alex J. Chen";
        String borrowerDept = "Junior • Computer Science";

        if (request.getBorrowerStudentId() != null) {
            Student student = studentRepository.findByStudentId(request.getBorrowerStudentId()).orElse(null);
            if (student != null) {
                borrowerName = student.getName();
                borrowerDept = student.getYear() + " • " + student.getDepartment();
            }
        }

        Loan loan = new Loan(
                item.getId(),
                item.getTitle(),
                item.getImage(),
                request.getBorrowerStudentId(),
                borrowerName,
                borrowerDept,
                item.getLenderStudentId() != null ? item.getLenderStudentId() : "owner-sarah",
                item.getLenderName(),
                item.getLenderDept(),
                request.getBorrowDays(),
                item.getDailyPrice(),
                item.getDepositHold(),
                item.getLocation(),
                request.getNote()
        );

        return loanRepository.save(loan);
    }

    public List<Loan> getBorrowingLoans(String studentId) {
        return loanRepository.findByBorrowerStudentId(studentId);
    }

    public List<Loan> getLendingLoans(String ownerStudentId) {
        return loanRepository.findByOwnerStudentIdAndStatus(ownerStudentId, LoanStatus.ACTIVE);
    }

    public List<Loan> getIncomingRequests(String ownerStudentId) {
        return loanRepository.findByOwnerStudentIdAndStatus(ownerStudentId, LoanStatus.REQUESTED);
    }

    public Loan decideLoan(String loanId, String decision) {
        Loan loan = loanRepository.findById(loanId)
                .orElseThrow(() -> new ResourceNotFoundException("Loan not found: " + loanId));

        if ("ACCEPT".equalsIgnoreCase(decision)) {
            loan.setStatus(LoanStatus.ACTIVE);
            loan.setApprovedAt(Instant.now());
            loan.setDueAt(Instant.now().plus(loan.getBorrowDays(), ChronoUnit.DAYS));

            // Mark item as unavailable while on loan
            itemRepository.findById(loan.getItemId()).ifPresent(item -> {
                item.setAvailable(false);
                itemRepository.save(item);
            });
        } else if ("DECLINE".equalsIgnoreCase(decision)) {
            loan.setStatus(LoanStatus.DECLINED);
        } else {
            throw new BadRequestException("Invalid decision: " + decision + ". Allowed values: ACCEPT, DECLINE");
        }

        return loanRepository.save(loan);
    }

    public Loan confirmReturn(String loanId) {
        Loan loan = loanRepository.findById(loanId)
                .orElseThrow(() -> new ResourceNotFoundException("Loan not found: " + loanId));

        loan.setStatus(LoanStatus.RETURNED);
        loan.setReturnedAt(Instant.now());

        // Make item available again
        itemRepository.findById(loan.getItemId()).ifPresent(item -> {
            item.setAvailable(true);
            itemRepository.save(item);
        });

        return loanRepository.save(loan);
    }
}

