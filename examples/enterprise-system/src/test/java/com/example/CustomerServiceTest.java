package com.example;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class CustomerServiceTest {
    @Test void registersAndFinds() {
        CustomerService service = new CustomerService();
        service.register("c1", "Alice");
        assertEquals("Alice", service.findName("c1").orElseThrow());
    }

    @Test void unknownCustomerIsEmpty() {
        CustomerService service = new CustomerService();
        assertTrue(service.findName("missing").isEmpty());
    }

    @Test void rejectsBlankId() {
        CustomerService service = new CustomerService();
        assertThrows(IllegalArgumentException.class, () -> service.register("", "Alice"));
    }

    @Test void rejectsBlankName() {
        CustomerService service = new CustomerService();
        assertThrows(IllegalArgumentException.class, () -> service.register("c1", ""));
    }
}
