package com.campuslend.controller;

import com.campuslend.dto.ApiResponse;
import com.campuslend.dto.LoanRequestDto;
import com.campuslend.model.Loan;
import com.campuslend.service.LoanService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/loans")
public class LoanController {

    private final LoanService loanService;

    @Autowired
    public LoanController(LoanService loanService) {
        this.loanService = loanService;
    }

    @PostMapping("/request")
    public ResponseEntity<ApiResponse<Loan>> createBorrowRequest(@Valid @RequestBody LoanRequestDto request) {
        Loan loan = loanService.createLoanRequest(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Borrow request submitted successfully", loan));
    }

    @GetMapping("/borrowing")
    public ResponseEntity<ApiResponse<List<Loan>>> getBorrowingLoans(
            @RequestParam(defaultValue = "SU-9824102") String studentId) {
        List<Loan> loans = loanService.getBorrowingLoans(studentId);
        return ResponseEntity.ok(ApiResponse.success(loans));
    }

    @GetMapping("/lending")
    public ResponseEntity<ApiResponse<List<Loan>>> getLendingLoans(
            @RequestParam(defaultValue = "SU-9824102") String studentId) {
        List<Loan> loans = loanService.getLendingLoans(studentId);
        return ResponseEntity.ok(ApiResponse.success(loans));
    }

    @GetMapping("/requests")
    public ResponseEntity<ApiResponse<List<Loan>>> getIncomingRequests(
            @RequestParam(defaultValue = "SU-9824102") String studentId) {
        List<Loan> loans = loanService.getIncomingRequests(studentId);
        return ResponseEntity.ok(ApiResponse.success(loans));
    }

    @PutMapping("/{id}/decision")
    public ResponseEntity<ApiResponse<Loan>> processDecision(
            @PathVariable String id,
            @RequestBody Map<String, String> body) {
        String decision = body.getOrDefault("decision", "ACCEPT");
        Loan loan = loanService.decideLoan(id, decision);
        return ResponseEntity.ok(ApiResponse.success("Loan request updated: " + decision, loan));
    }

    @PostMapping("/{id}/return")
    public ResponseEntity<ApiResponse<Loan>> confirmReturn(@PathVariable String id) {
        Loan loan = loanService.confirmReturn(id);
        return ResponseEntity.ok(ApiResponse.success("Item return confirmed and escrow deposit released", loan));
    }
}

