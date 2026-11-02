package com.campuslend.repository;

import com.campuslend.model.Notification;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface NotificationRepository extends MongoRepository<Notification, String> {

    List<Notification> findByRecipientStudentIdOrderByCreatedAtDesc(String recipientStudentId);

    List<Notification> findByRecipientStudentIdAndIsReadFalse(String recipientStudentId);
}

