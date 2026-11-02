package com.campuslend.repository;

import com.campuslend.model.Item;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ItemRepository extends MongoRepository<Item, String> {

    List<Item> findByCategory(String category);

    List<Item> findByIsAvailable(boolean isAvailable);

    List<Item> findByLenderStudentId(String lenderStudentId);

    List<Item> findByTitleContainingIgnoreCaseOrDescriptionContainingIgnoreCase(String title, String description);
}

