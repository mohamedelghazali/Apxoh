package com.example;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

public final class CustomerService {
    private final Map<String, String> customers = new HashMap<>();

    public void register(String id, String name) {
        if (id == null || id.isBlank()) {
            throw new IllegalArgumentException("id must not be blank");
        }
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("name must not be blank");
        }
        customers.put(id, name);
    }

    public Optional<String> findName(String id) {
        return Optional.ofNullable(customers.get(id));
    }
}
