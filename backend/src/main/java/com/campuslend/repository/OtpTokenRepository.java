package com.campuslend.repository;

import com.campuslend.model.OtpToken;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface OtpTokenRepository extends MongoRepository<OtpToken, String> {

    Optional<OtpToken> findByEmail(String email);

    Optional<OtpToken> findByEmailAndVerificationToken(String email, String verificationToken);

    void deleteByEmail(String email);
}

