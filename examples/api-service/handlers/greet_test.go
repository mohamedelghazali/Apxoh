package handlers

import (
    "net/http/httptest"
    "testing"
)

func TestGreetByName(t *testing.T) {
    req := httptest.NewRequest("GET", "/greet?name=Alice", nil)
    w := httptest.NewRecorder()
    Greet(w, req)
    if w.Body.String() != "Hello, Alice!" {
        t.Errorf("got %q", w.Body.String())
    }
}

func TestGreetFallback(t *testing.T) {
    req := httptest.NewRequest("GET", "/greet", nil)
    w := httptest.NewRecorder()
    Greet(w, req)
    if w.Body.String() != "Hello, stranger!" {
        t.Errorf("got %q", w.Body.String())
    }
}
